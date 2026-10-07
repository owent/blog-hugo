#!/usr/bin/env python3
"""Exercise the real Hugo templates and D2 CLI in an isolated miniature site."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SVG = "{http://www.w3.org/2000/svg}"


class D2Integration(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="test-blog-d2-")
        self.addCleanup(self.temporary.cleanup)
        self.site = Path(self.temporary.name)
        self.content = self.site / "source" / "post"
        self.content.mkdir(parents=True)
        self.config = self.site / "config.json"
        self.config.write_text(json.dumps({
            "baseURL": "https://example.org/blog/", "contentDir": "source",
            "markup": {"goldmark": {"parser": {"attribute": {"block": True}}}},
        }), encoding="utf-8")
        templates = ROOT / "themes" / "distinctionpp" / "layouts"
        for relative in (
            "partials/d2/render.html", "partials/diagrams/render.html", "_default/_markup/render-codeblock-d2.html",
            "_default/_markup/render-image.html", "shortcodes/d2.html",
        ):
            destination = self.site / "layouts" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(templates / relative, destination)
        (self.site / "layouts" / "_default" / "single.html").write_text(
            "<!doctype html><html><body>{{ .Content }}</body></html>", encoding="utf-8",
        )
        (self.site / "scripts").mkdir()
        shutil.copyfile(ROOT / "scripts" / "build-d2.py", self.site / "scripts" / "build-d2.py")
        self.article = self.content / "test.md"
        self.sidecar = self.content / "diagram.d2"
        self.sidecar.write_text('direction: right\na: 中文\nb: "<D2> & SVG"\na -> b\n', encoding="utf-8")

    def write_article(self, body):
        self.article.write_text('---\ntitle: D2 test\ndate: 2026-10-07\ntype: post\n---\n\n' + body,
                                encoding="utf-8")

    def build(self, success=True, args=()):
        result = subprocess.run(
            [sys.executable, str(self.site / "scripts" / "build-d2.py"),
             "--config", str(self.config), "--destination", str(self.site / "public"), *args],
            cwd=self.site, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            encoding="utf-8", errors="replace", timeout=120,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stdout)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result.stdout

    def assets(self):
        return {file.name: file.read_bytes() for file in (self.site / "assets" / "d2-generated").glob("*.svg")}

    def test_four_entries_and_distinct_ids(self):
        self.write_article('''![file alt](diagram.d2 "image title {max-width=720px}")

```d2 {alt="fence alt" max-width="600px"}
a: "<D2> & SVG"
a -> b
```

{{< d2 src="diagram.d2" alt="external alt" >}}{{< /d2 >}}

{{< d2 alt="inline alt" class="inline-test" >}}
x -> y
{{< /d2 >}}
''')
        self.build(args=("--minify",))
        assets = self.assets()
        self.assertEqual(len(assets), 4)
        ids = []
        for svg in assets.values():
            root = ET.fromstring(svg)
            self.assertEqual(root.tag, SVG + "svg")
            ids += [node.attrib["id"] for node in root.iter() if "id" in node.attrib]
        self.assertEqual(len(ids), len(set(ids)), "SVG IDs collide across diagram occurrences")
        html = (self.site / "public" / "post" / "test" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(html.count("data-d2-key="), 4)
        for label in ("file alt", "fence alt", "external alt", "inline alt", "image title", "inline-test"):
            self.assertIn(label, html)
        self.assertIn("中文", html)
        self.assertIn("&lt;D2", html)
        self.assertIn("min-width:", html)
        self.assertNotIn("d2-build/", html)
        self.assertNotIn(".wasm", html)
        self.assertFalse((self.site / "public" / "d2-build").exists())

    def test_relative_dependencies_are_rebuilt(self):
        sub = self.content / "sub"
        sub.mkdir()
        dependency = sub / "part.d2"
        dependency.write_text("label: Before\n", encoding="utf-8")
        (sub / "main.d2").write_text("box: @part\n", encoding="utf-8")
        (self.content / "part.d2").write_text("label: Inline import\n", encoding="utf-8")
        (sub / "icon.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30">'
            '<rect width="30" height="30" fill="red"/></svg>', encoding="utf-8",
        )
        self.write_article('''![import](sub/main.d2)

{{< d2 >}}
box: @part
{{< /d2 >}}

{{< d2 src="sub/icon.d2" >}}{{< /d2 >}}
''')
        (sub / "icon.d2").write_text("box: {icon: icon.svg}\n", encoding="utf-8")
        self.build()
        before = self.assets()
        self.assertIn(b"Before", b"".join(before.values()))
        self.assertIn(b"Inline import", b"".join(before.values()))
        self.assertIn(b"data:image/svg+xml;base64,", b"".join(before.values()))
        dependency.write_text("label: After\n", encoding="utf-8")
        self.build(args=("--renderToMemory",))
        after = self.assets()
        self.assertEqual(before.keys(), after.keys())
        self.assertNotEqual(before, after)
        self.assertIn(b"After", b"".join(after.values()))

    def test_failure_does_not_replace_assets_or_publish(self):
        self.write_article("```d2\nx -> y\n```\n")
        self.build()
        before = self.assets()
        final = self.site / "public" / "post" / "test" / "index.html"
        previous_html = final.read_bytes()
        self.write_article("```d2\nx: {\n```\n")
        self.assertIn("D2 failed", self.build(success=False))
        self.assertEqual(before, self.assets())
        self.assertEqual(previous_html, final.read_bytes())

    def test_missing_and_remote_sources_fail(self):
        for source in ("missing.d2", "https://example.org/remote.d2"):
            with self.subTest(source=source):
                self.write_article(f'![missing]({source})\n')
                output = self.build(success=False)
                self.assertTrue("source file not found" in output or "local path" in output, output)

    def test_stale_assets_are_removed(self):
        self.write_article("```d2\nx -> y\n```\n")
        self.build()
        before = self.assets()
        self.assertEqual(len(before), 1)
        self.write_article("```d2\na -> b\n```\n")
        self.build()
        assets = self.assets()
        self.assertEqual(len(assets), 1)
        self.assertFalse(set(before) & set(assets), "stale SVG was not removed")
        self.write_article("no diagrams\n")
        self.build()
        self.assertEqual(self.assets(), {})

    def test_direct_hugo_requires_preparation(self):
        self.write_article("```d2\nx -> y\n```\n")
        hugo = os.environ.get("HUGO_BINARY", "hugo")
        result = subprocess.run([hugo, "--renderToMemory"], cwd=self.site,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                encoding="utf-8", errors="replace", timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("D2 SVG missing", result.stdout)

    def test_environment_config_is_used_in_both_passes(self):
        staging = self.site / "config" / "staging"
        staging.mkdir(parents=True)
        (staging / "params.json").write_text('{"diagramlabel": "Staging"}', encoding="utf-8")
        self.write_article("{{< label >}}\n")
        (self.site / "layouts" / "shortcodes" / "label.html").write_text(
            '{{ partial "d2/render.html" (dict "page" .Page "source" '
            '(printf "x: %s" .Site.Params.diagramlabel) "instance" "environment") }}', encoding="utf-8",
        )
        self.build(args=("--environment=staging",))
        self.assertIn(b"Staging", b"".join(self.assets().values()))


if __name__ == "__main__":
    unittest.main()
