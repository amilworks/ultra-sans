"""Render the theme-aware README hero from its exact HTML source.

The renderer uses an installed Chromium-family browser and the committed WOFF2
artifacts. It writes fixed-size PNGs and a provenance manifest under
``docs/assets``.
"""

from __future__ import annotations

import argparse
import hashlib
import html.parser
import http.server
import json
import os
import shutil
import struct
import subprocess
import tempfile
import threading
import time
from functools import partial
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = Path(__file__).resolve()
ASSET_DIR = ROOT / "docs" / "assets"
SOURCE = ASSET_DIR / "readme-hero.html"
MANIFEST = ASSET_DIR / "readme-hero-manifest.json"
WIDTH = 2400
HEIGHT = 900
OUTPUTS = {
    "light": ASSET_DIR / "ultra-sans-hero-light.png",
    "dark": ASSET_DIR / "ultra-sans-hero-dark.png",
}
FONT_PATHS = [
    ROOT / "fonts" / "UltraSans-Variable.woff2",
    ROOT / "fonts" / "UltraSans-Italic-Variable.woff2",
]
EXACT_COPY = [
    "BisQue Ultra",
    "Variable typeface · Development 0.1",
    "Ultra Sans",
    "A variable typeface for an agentic system for science.",
    "Designed by Amil Khan · UCSB ECE",
]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


class VisibleTextParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.hidden_depth = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag in {"script", "style"}:
            self.hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self.hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth:
            self.parts.append(data)

    def normalized_text(self) -> str:
        return " ".join("".join(self.parts).split())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def browser_path() -> str:
    candidates = [
        os.environ.get("ULTRA_SANS_CHROME"),
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    raise SystemExit(
        "No Chromium-family browser found. Set ULTRA_SANS_CHROME to its executable."
    )


def png_dimensions(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"{path}: not a PNG")
    return struct.unpack(">II", header[16:24])


def exact_copy_problems() -> list[str]:
    parser = VisibleTextParser()
    parser.feed(SOURCE.read_text())
    visible_text = parser.normalized_text()
    return [
        f"source is missing exact copy: {text!r}"
        for text in EXACT_COPY
        if text not in visible_text
    ]


def verify_existing() -> list[str]:
    problems = exact_copy_problems()
    try:
        manifest = json.loads(MANIFEST.read_text())
    except (FileNotFoundError, json.JSONDecodeError) as error:
        return problems + [f"manifest cannot be read: {error}"]

    expected_source = str(SOURCE.relative_to(ROOT))
    if manifest.get("source") != expected_source:
        problems.append(f"manifest source is not {expected_source}")
    if manifest.get("source_sha256") != sha256(SOURCE):
        problems.append("manifest source digest is stale")
    if manifest.get("dimensions") != {"width": WIDTH, "height": HEIGHT}:
        problems.append(f"manifest dimensions are not {WIDTH}x{HEIGHT}")
    if manifest.get("exact_copy") != EXACT_COPY:
        problems.append("manifest exact-copy record is stale")

    expected_fonts = {
        str(path.relative_to(ROOT)): sha256(path) for path in FONT_PATHS
    }
    if manifest.get("font_inputs") != expected_fonts:
        problems.append("manifest font-input record is stale")

    exports = manifest.get("exports", {})
    for theme, path in OUTPUTS.items():
        if not path.exists():
            problems.append(f"{theme} export is missing")
            continue
        try:
            dimensions = png_dimensions(path)
        except SystemExit as error:
            problems.append(str(error))
            continue
        if dimensions != (WIDTH, HEIGHT):
            problems.append(f"{theme} export is {dimensions}; expected {(WIDTH, HEIGHT)}")
        expected_record = {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
        }
        if exports.get(theme) != expected_record:
            problems.append(f"manifest {theme} export record is stale")
    if not manifest.get("renderer"):
        problems.append("manifest renderer is missing")
    if manifest.get("render_script") != str(SCRIPT.relative_to(ROOT)):
        problems.append("manifest render-script path is stale")
    if manifest.get("render_script_sha256") != sha256(SCRIPT):
        problems.append("manifest render-script digest is stale")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    if args.verify_only:
        problems = verify_existing()
        if problems:
            print("README hero verification failed:")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        print("  verified README hero source, dimensions, and artifact digests")
        return 0

    browser = browser_path()
    copy_problems = exact_copy_problems()
    if copy_problems:
        raise SystemExit("README hero verification failed:\n  - " + "\n  - ".join(copy_problems))

    handler = partial(QuietHandler, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]

    try:
        with tempfile.TemporaryDirectory(prefix="ultra-sans-hero-") as profile:
            for theme, output in OUTPUTS.items():
                output.unlink(missing_ok=True)
                command = [
                    browser,
                    "--headless=new",
                    "--hide-scrollbars",
                    "--no-first-run",
                    "--disable-gpu",
                    "--disable-background-networking",
                    "--run-all-compositor-stages-before-draw",
                    "--virtual-time-budget=2500",
                    "--force-device-scale-factor=1",
                    f"--window-size={WIDTH},{HEIGHT}",
                    f"--user-data-dir={Path(profile) / theme}",
                    f"--screenshot={output}",
                    f"http://127.0.0.1:{port}/docs/assets/readme-hero.html?theme={theme}",
                ]
                process = subprocess.Popen(
                    command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                deadline = time.monotonic() + 20
                previous_size = None
                stable_samples = 0
                while time.monotonic() < deadline:
                    if output.exists() and output.stat().st_size:
                        current_size = output.stat().st_size
                        stable_samples = (
                            stable_samples + 1 if current_size == previous_size else 0
                        )
                        previous_size = current_size
                        if stable_samples >= 3:
                            break
                    if process.poll() is not None and not output.exists():
                        break
                    time.sleep(0.1)

                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                _, stderr = process.communicate()
                if not output.exists() or not output.stat().st_size:
                    raise SystemExit(
                        f"hero export failed for {theme}:\n{stderr.strip()}"
                    )
                dimensions = png_dimensions(output)
                if dimensions != (WIDTH, HEIGHT):
                    raise SystemExit(
                        f"{output}: rendered at {dimensions}; expected {(WIDTH, HEIGHT)}"
                    )
                print(f"  {output.relative_to(ROOT)}  {sha256(output)}")
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

    browser_version = subprocess.run(
        [browser, "--version"], capture_output=True, text=True, check=True
    ).stdout.strip()
    manifest = {
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": sha256(SOURCE),
        "dimensions": {"width": WIDTH, "height": HEIGHT},
        "exact_copy": EXACT_COPY,
        "font_inputs": {
            str(path.relative_to(ROOT)): sha256(path) for path in FONT_PATHS
        },
        "exports": {
            theme: {
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256(path),
            }
            for theme, path in OUTPUTS.items()
        },
        "renderer": browser_version,
        "render_script": str(SCRIPT.relative_to(ROOT)),
        "render_script_sha256": sha256(SCRIPT),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    problems = verify_existing()
    if problems:
        raise SystemExit("README hero verification failed:\n  - " + "\n  - ".join(problems))
    print(f"  {MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
