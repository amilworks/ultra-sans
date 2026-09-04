"""Record immutable protected-glyph evidence from the pre-refinement release.

This is a maintenance command, not part of make build/check; tests consume the
committed fixture and do not require Git history or network access.
"""
import hashlib
import io
import json
import subprocess
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parent.parent
REVISION = "3078939c29c3298954718a941e3d8dc9e0458525"
LOCATIONS = [(100, 9), (300, 9), (350, 13), (400, 14), (500, 16), (600, 13), (695, 24), (1000, 40)]
PROTECTED = "HIlnortfs?¿0123456789.,:;!"


def outline_signature(font, name):
    coords, ends, flags = font["glyf"][name].getCoordinates(font["glyf"])
    payload = [
        [[round(x, 5), round(y, 5)] for x, y in coords],
        list(ends), list(flags),
    ]
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()


def main():
    fixture = {"revision": REVISION, "locations": LOCATIONS, "protected": PROTECTED, "styles": {}}
    for style, filename in [("normal", "UltraSans-Variable.woff2"), ("italic", "UltraSans-Italic-Variable.woff2")]:
        raw = subprocess.check_output(["git", "show", f"{REVISION}:fonts/{filename}"], cwd=ROOT)
        cases = {}
        for weight, optical in LOCATIONS:
            font = instantiateVariableFont(TTFont(io.BytesIO(raw)), {"wght": weight, "opsz": optical}, inplace=True)
            cmap = font.getBestCmap()
            cases[f"{weight}/{optical}"] = {char: outline_signature(font, cmap[ord(char)]) for char in PROTECTED}
        fixture["styles"][style] = {"sha256": hashlib.sha256(raw).hexdigest(), "cases": cases}
    destination = ROOT / "font-lab/fixtures/protected-glyphs-0101.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(fixture, indent=2) + "\n")
    print(destination)


if __name__ == "__main__":
    main()
