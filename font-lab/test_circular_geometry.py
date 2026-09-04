"""Approved-study, optical-metric and interpolation regressions for 0.103."""
import json
import math
import unittest

import build_ultra_tabular as build
from circular_geometry import CIRCULAR_LETTERS, box, circular_points, split_contours
from record_refinement_baseline import outline_signature


class CircularTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = json.loads((build.ROOT / "font-lab/fixtures/circular-baseline-0102.json").read_text())
        cls.outputs = {source[4]: (build.BUILD_DIR / source[3]).read_bytes() for source in build.SOURCES}

    def cases(self):
        for style, data in self.baseline["styles"].items():
            for location, case in data["cases"].items():
                weight, optical = map(int, location.split("/"))
                font = build._instance(self.outputs[style], "circle-test", {"wght": weight, "opsz": optical})
                yield style, location, case, font

    def test_selected_roman_study_is_adopted_exactly(self):
        for style, location, case, font in self.cases():
            if style != "normal":
                continue
            for char, expected in case["selected_study"].items():
                name = font.getBestCmap()[ord(char)]
                self.assertEqual(outline_signature(font, name), expected["outline"], (location, char))
                self.assertEqual(font["hmtx"][name][0], expected["advance"], (location, char))

    def test_other_defining_letters_and_spacing_are_unchanged(self):
        for style, location, case, font in self.cases():
            for char, expected in case["protected"].items():
                name = font.getBestCmap()[ord(char)]
                self.assertEqual(outline_signature(font, name), expected["outline"], (style, location, char))
                self.assertEqual(font["hmtx"][name][0], expected["advance"], (style, location, char))

    def test_strokes_overshoot_side_space_and_diagonals_are_preserved(self):
        for style, location, case, font in self.cases():
            for char, expected in case["circular"].items():
                name = font.getBestCmap()[ord(char)]
                coords, ends, flags = font["glyf"][name].getCoordinates(font["glyf"])
                contours = split_contours(coords, ends, flags, style == "italic")
                outer, inner = [box(points) for points, _ in contours[:2]]
                old_outer, old_inner = expected["outer"], expected["inner"]
                old_width = old_outer[2] - old_outer[0]
                height = old_outer[3] - old_outer[1]
                delta = height - old_width
                ctx = (style, location, char)
                self.assertAlmostEqual(outer[0], old_outer[0], delta=2, msg=ctx)
                self.assertAlmostEqual(outer[1], old_outer[1], delta=1.5, msg=ctx)
                self.assertAlmostEqual(outer[3], old_outer[3], delta=1.5, msg=ctx)
                self.assertAlmostEqual(font["hmtx"][name][0], expected["advance"] + delta, delta=2, msg=ctx)
                for axis in (0, 1):
                    stroke = ((outer[axis + 2] - outer[axis]) - (inner[axis + 2] - inner[axis])) / 2
                    old_stroke = ((old_outer[axis + 2] - old_outer[axis]) - (old_inner[axis + 2] - old_inner[axis])) / 2
                    self.assertAlmostEqual(stroke, old_stroke, delta=2, msg=ctx)
                self.assertEqual(len(contours) - 2, len(expected["extras"]))
                for (points, _), old_points in zip(contours[2:], expected["extras"]):
                    self.assertEqual(len(points), len(old_points))
                    for (x, y), (old_x, old_y) in zip(points, old_points):
                        self.assertAlmostEqual(x, old_x + delta / 2, delta=2, msg=ctx)
                        self.assertAlmostEqual(y, old_y, delta=1.5, msg=ctx)

    def test_circular_interpolation_and_counter_winding(self):
        for style, raw in self.outputs.items():
            for optical in (9, 12, 14, 16, 20, 24, 32, 40):
                for weight in (100, 250, 300, 350, 400, 430, 500, 600, 695, 850, 1000):
                    font = build._instance(raw, "circle-test", {"wght": weight, "opsz": optical})
                    for char in CIRCULAR_LETTERS:
                        name = font.getBestCmap()[ord(char)]
                        coords, ends, flags = font["glyf"][name].getCoordinates(font["glyf"])
                        contours = split_contours(coords, ends, flags, style == "italic")
                        ctx = (style, weight, optical, char)
                        outer, inner = [box(points) for points, _ in contours[:2]]
                        width, height = outer[2] - outer[0], outer[3] - outer[1]
                        self.assertAlmostEqual(width, height, delta=2, msg=ctx)
                        cx, cy = (outer[0] + outer[2]) / 2, (outer[1] + outer[3]) / 2
                        for (x, y), on_curve in zip(*contours[0]):
                            if on_curve:
                                self.assertAlmostEqual(math.hypot(x - cx, y - cy), height / 2, delta=2, msg=ctx)
                        self.assertGreater(inner[2] - inner[0], 0, ctx)
                        self.assertGreater(inner[3] - inner[1], 0, ctx)
                        for (points, _), direction in zip(contours[:2], (-1, 1)):
                            signed = sum(x * points[(i + 1) % len(points)][1] - points[(i + 1) % len(points)][0] * y for i, (x, y) in enumerate(points))
                            self.assertGreater(signed * direction, 0, ctx)
                        if char not in "Oo":
                            self.assertTrue(flags[0] & 0x40, ctx)

    def test_unrecognized_source_topology_fails_closed(self):
        for char in ("O", "x", "ø"):
            with self.assertRaises(ValueError):
                circular_points(char, [], [], [])


if __name__ == "__main__":
    unittest.main()
