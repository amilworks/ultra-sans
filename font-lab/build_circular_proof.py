"""Embed the approved 0.102 baseline and actual 0.103 artifacts in a proof."""
import io
import subprocess

from fontTools.ttLib import TTFont

import build_ultra_tabular as build
from build_refinement_proof import font_data, REFINED_REVISION


def main():
    here = build.ROOT / "font-lab"
    template = (here / "circular.template.html").read_text()
    for style, suffix in [("NORMAL", ""), ("ITALIC", "-Italic")]:
        name = f"UltraSans{suffix}-Variable.woff2"
        before = subprocess.check_output(["git", "show", f"{REFINED_REVISION}:fonts/{name}"], cwd=build.ROOT)
        template = template.replace(f"{{{{BEFORE_{style}}}}}", font_data(TTFont(io.BytesIO(before), recalcTimestamp=False), [0x2082, 0x2212]))
        current = TTFont(build.BUILD_DIR / name, recalcTimestamp=False)
        if current["name"].getDebugName(5) != "Version 0.103":
            raise SystemExit("Build both 0.103 artifacts before generating their proof")
        template = template.replace(f"{{{{AFTER_{style}}}}}", font_data(current, [0x2082, 0x2212]))
    if "{{" in template:
        raise SystemExit("unexpanded circular proof token")
    destination = here / "circular.html"
    destination.write_text(template)
    print(destination)


if __name__ == "__main__":
    main()
