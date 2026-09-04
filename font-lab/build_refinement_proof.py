"""Create an embedded before/after proof, including an O/o-only circle study."""
import argparse
import base64
import io
import math
import subprocess
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.models import VariationModel

import build_ultra_tabular as build
from record_refinement_baseline import REVISION

HERE = Path(__file__).parent
REFINED_REVISION = "0820c8e2bdeaf23392c50c9ed18aa6e6d3071a82"


def ellipse(cx, cy, rx, ry, clockwise):
    """16 fixed quadratic arc segments: consistent topology at every master."""
    points, flags = [], []
    direction = -1 if clockwise else 1
    step = direction * math.tau / 16
    for index in range(16):
        angle = step * index
        points.append((cx + rx * math.cos(angle), cy + ry * math.sin(angle)))
        flags.append(1)
        midpoint = angle + step / 2
        correction = 1 / math.cos(step / 2)
        points.append((cx + rx * math.cos(midpoint) * correction, cy + ry * math.sin(midpoint) * correction))
        flags.append(0)
    return points, flags


def circle_study(raw, fraction):
    """An isolated shape study, not an installed or shipping font.

    Outer proportions approach a circle. Independent horizontal and vertical
    stroke thicknesses are retained; this is not a heavy monoline ring.
    Only O/o change; the unsynchronized C/G explain the family-level tradeoff.
    """
    font = TTFont(io.BytesIO(raw), recalcTimestamp=False)
    model = VariationModel([norm for norm, _ in build.MASTER_GRID])
    for char in "Oo":
        samples = []
        name = font.getBestCmap()[ord(char)]
        for _, (weight, optical) in build.MASTER_GRID:
            source = build._instance(raw, "circle-study", {"wght": weight, "opsz": optical})
            glyph = source["glyf"][name]
            coords, ends, _ = glyph.getCoordinates(source["glyf"])
            contours, start = [], 0
            for end in ends:
                pts = list(coords[start:end + 1])
                contours.append((min(x for x, _ in pts), min(y for _, y in pts), max(x for x, _ in pts), max(y for _, y in pts)))
                start = end + 1
            contours.sort(key=lambda box: (box[2] - box[0]) * (box[3] - box[1]), reverse=True)
            outer, inner = contours
            old_width, height = outer[2] - outer[0], outer[3] - outer[1]
            width = old_width + fraction * (height - old_width)
            side_stroke = (old_width - (inner[2] - inner[0])) / 2
            top_stroke = (height - (inner[3] - inner[1])) / 2
            cx, cy = outer[0] + width / 2, (outer[1] + outer[3]) / 2
            outside, outer_flags = ellipse(cx, cy, width / 2, height / 2, True)
            inside, inner_flags = ellipse(cx, cy, width / 2 - side_stroke, height / 2 - top_stroke, False)
            samples.append((outside + inside, [31, 63], bytes(outer_flags + inner_flags), source["hmtx"][name][0] + width - old_width))
        build._replace_outline(font, name, samples, model)
    return font


def font_data(font, extra_unicodes=()):
    options = subset.Options()
    options.layout_features = ["*"]
    sub = subset.Subsetter(options=options)
    sub.populate(unicodes=list(range(32, 383)) + [0x2013, 0x2014, 0x2019, 0x2026] + list(extra_unicodes))
    sub.subset(font)
    font.flavor = "woff2"
    buffer = io.BytesIO()
    font.save(buffer)
    return base64.b64encode(buffer.getvalue()).decode()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "refinements.html")
    args = parser.parse_args()
    template = (HERE / "refinements.template.html").read_text()
    # This is an archived experiment. Never relabel a newer release as 0.102.
    current_raw = subprocess.check_output(["git", "show", f"{REFINED_REVISION}:fonts/UltraSans-Variable.woff2"], cwd=build.ROOT)
    for style, suffix in [("NORMAL", ""), ("ITALIC", "-Italic")]:
        name = f"UltraSans{suffix}-Variable.woff2"
        before = subprocess.check_output(["git", "show", f"{REVISION}:fonts/{name}"], cwd=build.ROOT)
        template = template.replace(f"{{{{BEFORE_{style}}}}}", font_data(TTFont(io.BytesIO(before), recalcTimestamp=False)))
        refined = subprocess.check_output(["git", "show", f"{REFINED_REVISION}:fonts/{name}"], cwd=build.ROOT)
        template = template.replace(f"{{{{AFTER_{style}}}}}", font_data(TTFont(io.BytesIO(refined), recalcTimestamp=False)))
    for key, fraction in [("ROUNDER", .45), ("CIRCLE", 1.0)]:
        template = template.replace(f"{{{{{key}}}}}", font_data(circle_study(current_raw, fraction)))
    if "{{" in template:
        raise SystemExit("unexpanded proof token")
    args.output.write_text(template)
    print(args.output)


if __name__ == "__main__":
    main()
