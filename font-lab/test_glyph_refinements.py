"""Contract and interpolation tests for Ultra Sans 0.102."""
import json
import unittest
import unicodedata

from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen

import build_ultra_tabular as build
from glyph_refinements import REFINED_LETTERS, refine_points, tabular_one_points
from record_refinement_baseline import outline_signature


def bounds(font, name):
    glyphs = font.getGlyphSet()
    pen = BoundsPen(glyphs)
    glyphs[name].draw(pen)
    return pen.bounds


def area(font, name):
    glyphs = font.getGlyphSet()
    pen = AreaPen(glyphs)
    glyphs[name].draw(pen)
    return abs(pen.value)


class RefinementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = {}
        cls.outputs = {}
        for source in build.SOURCES:
            cls.inputs[source[4]] = build.fetch_source(*source[:3])
            cls.outputs[source[4]] = (build.BUILD_DIR / source[3]).read_bytes()

    def test_instance_cache_is_source_specific(self):
        location = {"wght": 400, "opsz": 14}
        upright = build._instance(self.inputs["normal"], "same-key", location)
        italic = build._instance(self.inputs["italic"], "same-key", location)
        self.assertIsNot(upright, italic)
        self.assertEqual(upright["post"].italicAngle, 0)
        self.assertAlmostEqual(italic["post"].italicAngle, -10, places=2)

    def test_all_masters_have_compatible_authored_topology(self):
        for style, raw in self.inputs.items():
            italic = style == "italic"
            expected = {}
            for _, (weight, optical) in build.MASTER_GRID:
                source = build._instance(raw, "test-source", {"wght": weight, "opsz": optical})
                cmap = source.getBestCmap()
                for char in REFINED_LETTERS:
                    coords, ends, flags = source["glyf"][cmap[ord(char)]].getCoordinates(source["glyf"])
                    points, ends, flags = refine_points(char, coords, ends, flags, build._measures(source)["stem"], optical, italic)
                    topology = (len(points), tuple(ends), flags)
                    expected.setdefault(char, topology)
                    self.assertEqual(topology, expected[char], (style, weight, optical, char))
                coords, ends, flags = source["glyf"][cmap[ord("1")]].getCoordinates(source["glyf"])
                points, ends, flags = tabular_one_points(coords, ends, flags, source["hmtx"][cmap[ord("0")]][0], italic)
                self.assertEqual((len(points), ends), (11, [10]))

    def test_unknown_source_topology_fails_closed(self):
        with self.assertRaises(ValueError):
            refine_points("a", [], [], [], 84, 14)
        with self.assertRaises(ValueError):
            tabular_one_points([], [], [], 684)

    def test_upstream_kerning_is_retained(self):
        for style in self.outputs:
            for weight, optical in ((400, 14), (500, 16), (600, 13), (1000, 40)):
                loc = {"wght": weight, "opsz": optical}
                source = build._instance(self.inputs[style], "test-source", loc)
                output = build._instance(self.outputs[style], "test-output", loc)
                self.assertEqual(output["GPOS"].compile(output), source["GPOS"].compile(source), (style, loc))

    def test_protected_glyphs_are_unchanged_from_approved_release(self):
        fixture = json.loads((build.ROOT / "font-lab/fixtures/protected-glyphs-0101.json").read_text())
        for style, data in fixture["styles"].items():
            for location, expected in data["cases"].items():
                weight, optical = map(int, location.split("/"))
                font = build._instance(self.outputs[style], "test-output", {"wght": weight, "opsz": optical})
                cmap = font.getBestCmap()
                for char, signature in expected.items():
                    self.assertEqual(outline_signature(font, cmap[ord(char)]), signature, (style, location, char))

    def test_text_openings_increase_without_global_weight_change(self):
        for style in self.outputs:
            for weight, optical in ((400, 14), (500, 16), (600, 13)):
                loc = {"wght": weight, "opsz": optical}
                before = build._instance(self.inputs[style], "test-source", loc)
                after = build._instance(self.outputs[style], "test-output", loc)
                for char in "aeg":
                    name = after.getBestCmap()[ord(char)]
                    fraction = area(after, name) / area(before, name)
                    self.assertGreater(fraction, .94, (style, loc, char, fraction))
                    self.assertLess(fraction, 1.0, (style, loc, char, fraction))
                for char, index in [("a", 16), ("e", 35 if style == "italic" else 33)]:
                    name = after.getBestCmap()[ord(char)]
                    old = before["glyf"][name].getCoordinates(before["glyf"])[0]
                    new = after["glyf"][name].getCoordinates(after["glyf"])[0]
                    delta = new[index][1] - old[index][1]
                    self.assertGreater(delta if char == "a" else -delta, 4)

    def test_interpolation_metrics_and_outlines(self):
        # Includes masters, real UI tokens, and off-master positions.
        for style in self.outputs:
            for optical in (9, 12, 14, 16, 20, 24, 32, 40):
                for weight in (100, 250, 300, 350, 400, 430, 500, 600, 695, 850, 1000):
                    loc = {"wght": weight, "opsz": optical}
                    font = build._instance(self.outputs[style], "test-output", loc)
                    source = build._instance(self.inputs[style], "test-source", loc)
                    cmap = font.getBestCmap()
                    zero_width = font["hmtx"][cmap[ord("0")]][0]
                    for digit in build.DIGITS:
                        name = cmap[ord(digit)]
                        self.assertEqual(font["hmtx"][name + ".tnum"][0], zero_width, (style, loc, digit))
                    one = cmap[ord("1")] + ".tnum"
                    box = bounds(font, one)
                    self.assertGreater(box[0], 0)
                    self.assertLess(box[2], zero_width)
                    self.assertGreater((box[2] - box[0]) / zero_width, .50)
                    # Extremum ownership can change between masters, so exact
                    # ink-centering is nonlinear. Bound drift to <0.1px at 16px.
                    self.assertLess(abs((box[0] + box[2]) / 2 - zero_width / 2), 6.25, (style, loc))
                    self.assertFalse(font["glyf"][one].isComposite())
                    self.assertEqual(font["glyf"][one].numberOfContours, 1)
                    for char in REFINED_LETTERS:
                        name = cmap[ord(char)]
                        before, after = bounds(source, name), bounds(font, name)
                        self.assertLessEqual(abs(before[1] - after[1]), 2, (style, loc, char, "bottom"))
                        self.assertLessEqual(abs(before[3] - after[3]), 2, (style, loc, char, "top"))
                        self.assertLessEqual(abs(font["hmtx"][name][0] - source["hmtx"][name][0]), 2)
                    # A rebuilt small-size curve must not collapse.
                    for char in "aegRS":
                        name = cmap[ord(char)]
                        self.assertGreater(area(font, name), 0)

    def test_composite_advances_track_their_refitted_base(self):
        for style in self.outputs:
            for weight, optical in ((100, 9), (400, 14), (500, 16), (600, 24), (1000, 40)):
                loc = {"wght": weight, "opsz": optical}
                output = build._instance(self.outputs[style], "test-output", loc)
                source = build._instance(self.inputs[style], "test-source", loc)
                cmap = output.getBestCmap()
                for char in "COGØaegRS":
                    base_name = cmap[ord(char)]
                    base_delta = output["hmtx"][base_name][0] - source["hmtx"][base_name][0]
                    for codepoint, name in source.getBestCmap().items():
                        decomposition = unicodedata.normalize("NFD", chr(codepoint))
                        if not (len(decomposition) > 1 and decomposition[0] == char):
                            continue  # diacritics, not multi-letter composites such as Rs
                        glyph = source["glyf"][name]
                        if glyph.isComposite() and any(c.glyphName == base_name for c in glyph.components):
                            delta = output["hmtx"][name][0] - source["hmtx"][name][0]
                            self.assertLessEqual(abs(delta - base_delta), 2, (style, loc, char, name))


if __name__ == "__main__":
    unittest.main()
