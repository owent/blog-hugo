#!/usr/bin/env python3
"""Real PlantUML/Hugo integration, reusing the isolated D2 site fixture."""
import importlib.util
from pathlib import Path
import shutil
import sys
import unittest
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("d2_tests", Path(__file__).with_name("test-d2.py"))
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


class PlantUMLIntegration(unittest.TestCase):
    write_article = fixture.D2Integration.write_article
    build = fixture.D2Integration.build

    def setUp(self):
        fixture.D2Integration.setUp(self)
        for relative in ("partials/plantuml/render.html", "_default/_markup/render-codeblock-plantuml.html",
                         "shortcodes/plantuml.html"):
            target = self.site / "layouts" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(fixture.ROOT / "themes/distinctionpp/layouts" / relative, target)
        self.sidecar = self.content / "diagram.puml"
        self.sidecar.write_text('@startuml\nAlice -> Bob: 中文 & SVG\n@enduml\n', encoding="utf-8")

    def assets(self):
        return {p.name: p.read_bytes() for p in (self.site / "assets/plantuml-generated").glob("*.svg")}

    def test_four_entries_ids_themes_and_graphviz(self):
        self.write_article('''![file alt](diagram.puml "title {max-width=720px}")

```plantuml {alt="fence alt"}
@startuml
component "服务" as A
database "数据库" as B
A --> B
@enduml
```

{{< plantuml src="diagram.puml" alt="external alt" >}}{{< /plantuml >}}

{{< plantuml alt="inline alt" >}}
@startuml
!theme cerulean-outline
Alice -> Bob: Custom theme
@enduml
{{< /plantuml >}}
''')
        self.build(args=("--minify",))
        self.assertEqual(len(self.assets()), 4)
        ids = []
        for svg in self.assets().values():
            root = ET.fromstring(svg)
            ids.extend(node.attrib["id"] for node in root.iter() if "id" in node.attrib)
            text = "".join(root.itertext())
            self.assertIn("min-width:", root.attrib["style"])
            if "Custom theme" in text:
                self.assertIn(b"#2FA4E7", svg)
            else:
                self.assertNotIn(b"#2FA4E7", svg)
        self.assertEqual(len(ids), len(set(ids)))
        html = (self.site / "public/post/test/index.html").read_text(encoding="utf-8")
        for alt in ("file alt", "fence alt", "external alt", "inline alt"):
            self.assertIn(alt, html)
        self.assertFalse((self.site / "public/plantuml-build").exists())

    def test_local_include_rebuild_and_long_extension(self):
        sub = self.content / "sub"
        sub.mkdir()
        (sub / "main.plantuml").write_text('@startuml\n!include part.puml\n@enduml', encoding="utf-8")
        part = sub / "part.puml"
        part.write_text('Alice -> Bob: Before', encoding="utf-8")
        self.write_article('![include](sub/main.plantuml)')
        self.build()
        self.assertIn(b"Before", b"".join(self.assets().values()))
        part.write_text('Alice -> Bob: After', encoding="utf-8")
        self.build()
        self.assertIn(b"After", b"".join(self.assets().values()))
        self.assertNotIn(b"Before", b"".join(self.assets().values()))

    def test_failure_preserves_outputs_and_rejects_remote_include(self):
        self.write_article('![diagram](diagram.puml)')
        self.build()
        assets = self.assets()
        final = self.site / "public/post/test/index.html"
        previous = final.read_bytes()
        for source in ('@startuml\nnot a valid diagram ???\n@enduml',
                       '@startuml\n!includeurl https://example.org/no-network.puml\n@enduml',
                       'Alice -> Bob', '@startuml\nA -> B\n@enduml\n@startuml\nB -> C\n@enduml'):
            with self.subTest(source=source):
                self.write_article('```plantuml\n' + source + '\n```')
                self.build(success=False)
                self.assertEqual(self.assets(), assets)
                self.assertEqual(final.read_bytes(), previous)

    def test_missing_file_and_stale_cleanup(self):
        self.write_article('![diagram](missing.puml)')
        self.assertIn("source file not found", self.build(success=False))
        self.write_article('![diagram](diagram.puml)')
        self.build()
        self.write_article('No diagrams')
        self.build()
        self.assertEqual(self.assets(), {})


if __name__ == "__main__":
    unittest.main()
