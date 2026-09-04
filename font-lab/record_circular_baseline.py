"""Maintenance only: pin 0.102 shapes and the originally selected circle study.

Tests consume this committed JSON without Git history or network access. Never
regenerate it as part of a build/check: it is independent pre-change evidence.
"""
import hashlib
import io
import json
import subprocess

from fontTools.ttLib import TTFont

import build_ultra_tabular as build
from build_refinement_proof import circle_study
from circular_geometry import CIRCULAR_LETTERS, RING_INDICES, box, split_contours
from record_refinement_baseline import LOCATIONS, outline_signature

REVISION = "0820c8e2bdeaf23392c50c9ed18aa6e6d3071a82"
PROTECTED = "ABCDEFGHIJKLMNPRSTUVWXYZabcdefghijklmnpqrstuvwxyz?¿0123456789.,:;!"


def main():
    locations = sorted(set(LOCATIONS + [location for _, location in build.MASTER_GRID]))
    fixture = {"revision": REVISION, "protected": PROTECTED, "styles": {}}
    for source in build.SOURCES:
        filename, style = source[3:]
        raw = subprocess.check_output(["git", "show", f"{REVISION}:fonts/{filename}"], cwd=build.ROOT)
        cases = {}
        if style == "normal":
            selected = circle_study(raw, 1)
            buffer = io.BytesIO()
            selected.save(buffer)
            study_raw = buffer.getvalue()
        for weight, optical in locations:
            loc = {"wght": weight, "opsz": optical}
            font = build._instance(raw, "circular-baseline", loc)
            cmap = font.getBestCmap()
            circular = {}
            for char in CIRCULAR_LETTERS:
                name = cmap[ord(char)]
                coords, ends, flags = font["glyf"][name].getCoordinates(font["glyf"])
                contours = split_contours(coords, ends, flags, style == "italic")
                outer, inner = [box(contours[i][0]) for i in RING_INDICES[char]]
                circular[char] = {"outer": outer, "inner": inner, "advance": font["hmtx"][name][0], "extras": [points for i, (points, _) in enumerate(contours) if i not in RING_INDICES[char]]}
            case = {"protected": {char: {"outline": outline_signature(font, cmap[ord(char)]), "advance": font["hmtx"][cmap[ord(char)]][0]} for char in PROTECTED}, "circular": circular}
            if style == "normal":
                study = build._instance(study_raw, "selected-circle", loc)
                case["selected_study"] = {char: {"outline": outline_signature(study, cmap[ord(char)]), "advance": study["hmtx"][cmap[ord(char)]][0]} for char in "Oo"}
            cases[f"{weight}/{optical}"] = case
        fixture["styles"][style] = {"sha256": hashlib.sha256(raw).hexdigest(), "cases": cases}
    destination = build.ROOT / "font-lab/fixtures/circular-baseline-0102.json"
    destination.write_text(json.dumps(fixture, indent=2) + "\n")
    print(destination)


if __name__ == "__main__":
    main()
