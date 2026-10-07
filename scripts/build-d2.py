#!/usr/bin/env python3
"""Build D2 and PlantUML SVGs, then run Hugo (historical command name retained)."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]


def collection_args(args):
    """Keep content selection flags, but isolate collection from the final output."""
    result = []
    i = 0
    while i < len(args):
        arg = args[i]
        name = arg.split("=", 1)[0]
        if name in ("server", "--watch", "-w", "--source", "-s"):
            raise ValueError("Use this wrapper for one-shot builds in the repository root")
        if name in ("--destination", "-d"):
            if "=" not in arg:
                i += 1
                if i == len(args):
                    raise ValueError(f"Missing value for {arg}")
        elif name not in ("--renderToMemory", "-M", "--gc", "--cleanDestinationDir", "--minify"):
            result.append(arg)
        i += 1
    return result


def collection_config(args, overlay):
    """Append a collection overlay without changing the user's Hugo environment."""
    result = []
    config = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--config":
            i += 1
            if i == len(args):
                raise ValueError("Missing value for --config")
            config = args[i]
        elif arg.startswith("--config="):
            config = arg.split("=", 1)[1]
        else:
            result.append(arg)
        i += 1
    if config is None:
        config = next((name for name in (
            "hugo.toml", "hugo.yaml", "hugo.json", "config.toml", "config.yaml", "config.json",
        ) if (ROOT / name).is_file()), None)
    if not config:
        raise ValueError("No Hugo config found; pass --config explicitly")
    return [*result, f"--config={config},{overlay}"]


def executable(variable, default):
    name = os.environ.get(variable, default)
    found = shutil.which(name)
    if not found:
        raise ValueError(f"{name} not found; install it or set {variable} to its executable path")
    return found


def remove_stale(output_dir, current):
    """Drop SVGs left behind by diagrams that no longer exist."""
    removed = 0
    for filename in output_dir.glob("*.svg"):
        if re.fullmatch(r"[a-f0-9]{64}", filename.stem) and filename.stem not in current:
            filename.unlink()
            removed += 1
    if removed:
        print(f"Removed {removed} stale SVGs from {output_dir.name}", flush=True)


def plantuml_command():
    jar = Path(os.environ.get("PLANTUML_JAR", "plantuml.jar")).resolve()
    if not jar.is_file():
        raise ValueError("PlantUML JAR not found; set PLANTUML_JAR to its local path")
    return [executable("JAVA_BINARY", "java"), "-Djava.awt.headless=true",
            "-DPLANTUML_SECURITY_PROFILE=ALLOWLIST", f"-Dplantuml.allowlist.path={ROOT}",
            "-jar", str(jar), "--svg", "--pipe", "--charset", "UTF-8",
            "--stop-on-error", "--no-error-image", "--disable-metadata",
            "--theme", "plain"]


def render_requests(request_dir, command, engine):
    """Re-render every request, including imported files and local image changes."""
    requests = sorted(request_dir.glob("*.json"))
    rendered = []
    for filename in requests:
        key = filename.stem
        if not re.fullmatch(r"[a-f0-9]{64}", key):
            raise ValueError(f"Invalid {engine} request name: {filename.name}")
        request = json.loads(filename.read_text(encoding="utf-8"))
        directory = Path(request["baseDir"]).resolve()
        if not directory.is_relative_to(ROOT) or not directory.is_dir():
            raise ValueError(f"{engine} source directory must be inside the repository: {directory}")
        print(f"{engine}: {request['instance']}", flush=True)
        source = request["source"]
        if engine == "PlantUML":
            # A single SVG per occurrence; reject silent empty/multi-diagram output.
            if len(re.findall(r"(?m)^\s*@startuml\b", source)) != 1 or len(re.findall(r"(?m)^\s*@enduml\b", source)) != 1:
                raise ValueError(f"PlantUML requires one @startuml/@enduml pair: {request['instance']}")
            args = command
        else:
            args = [*command, "--target=", "--bundle=true", "--no-xml-tag=true", f"--salt={key}",
                    "--timeout=60", "-", "-"]
        # stdin uses the source directory for relative imports and image assets.
        result = subprocess.run(
            args, cwd=directory, input=source.encode("utf-8"),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=75, check=False,
        )
        if result.returncode:
            sys.stderr.write(result.stderr.decode("utf-8", errors="replace"))
            raise ValueError(f"{engine} failed for {request['instance']} (exit {result.returncode})")
        svg = result.stdout
        root = ET.fromstring(svg)
        if root.tag != "{http://www.w3.org/2000/svg}svg":
            raise ValueError(f"{engine} did not return SVG for {request['instance']}")
        # Keep text at its original size on narrow screens; the container scrolls.
        width = float(root.attrib["viewBox"].split()[2])
        if not 0 < width < float("inf"):
            raise ValueError(f"Invalid SVG width for {request['instance']}")
        style = f"display: block; width: 100%; height: auto; min-width: {width:g}px;"
        if engine == "PlantUML":
            # Prefix local IDs and references, preserving external links and colors.
            ids = {node.attrib["id"]: f"puml-{key}-{node.attrib['id']}"
                   for node in root.iter() if "id" in node.attrib}
            for node in root.iter():
                for attr, value in list(node.attrib.items()):
                    if attr == "id":
                        node.set(attr, ids[value])
                    else:
                        value = re.sub(r"url\(#([^)]*)\)", lambda m: f"url(#{ids.get(m[1], m[1])})", value)
                        if attr.endswith("href") and value.startswith("#") and value[1:] in ids:
                            value = "#" + ids[value[1:]]
                        node.set(attr, value)
            root.set("style", style)
            ET.register_namespace("", "http://www.w3.org/2000/svg")
            ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
            svg = ET.tostring(root, encoding="utf-8")
        else:
            svg = svg.replace(b"<svg", f'<svg style="{style}"'.encode("ascii"), 1)
        rendered.append((key, svg))
    print(f"Rendered {len(rendered)} {engine} diagrams", flush=True)
    return rendered


def publish(output_dir, rendered):
    output_dir.mkdir(parents=True, exist_ok=True)
    for key, svg in rendered:
        target = output_dir / f"{key}.svg"
        temporary = target.with_suffix(".svg.tmp")
        temporary.write_bytes(svg)
        temporary.replace(target)
    remove_stale(output_dir, {key for key, _ in rendered})


def main(args):
    os.chdir(ROOT)
    collect = collection_args(args)
    hugo = executable("HUGO_BINARY", "hugo")
    with tempfile.TemporaryDirectory(prefix="blog-d2-") as temporary:
        overlay = Path(temporary) / "d2-collect.json"
        overlay.write_text(json.dumps({"params": {
            "d2": {"collect": True}, "plantuml": {"collect": True},
        }}), encoding="utf-8")
        destination = Path(temporary) / "collect"
        subprocess.run(
            [hugo, *collection_config(collect, overlay), f"--destination={destination}"],
            check=True,
        )
        batches = []
        for engine, label in (("d2", "D2"), ("plantuml", "PlantUML")):
            request_dir = destination / f"{engine}-build"
            output_dir = ROOT / "assets" / f"{engine}-generated"
            rendered = []
            if any(request_dir.glob("*.json")):
                command = [executable("D2_BINARY", "d2")] if engine == "d2" else plantuml_command()
                rendered = render_requests(request_dir, command, label)
            batches.append((output_dir, rendered))
        # Both engines must succeed before replacing assets or final HTML.
        for output_dir, rendered in batches:
            publish(output_dir, rendered)
    subprocess.run([hugo, *args], check=True)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except (ValueError, KeyError, OSError, ET.ParseError, subprocess.SubprocessError) as error:
        print(f"Diagram build failed: {error}", file=sys.stderr)
        sys.exit(1)
