"""Ultra's small-size details and signature strokes, on pinned DM topology.

This module describes bounded point edits, not a generic outline distortion.
Indices below are semantic landmarks in the SHA-pinned upstream DM masters.
Topology is checked before editing, and the same recipe runs at every master.
All distances are font units (the DM source has a 1000-unit em).
"""
from __future__ import annotations

import math


TOPOLOGY = {
    False: {"a": (33, 48), "e": (37,), "g": (45, 61, 73, 77), "R": (12, 16, 25), "S": (50,)},
    True: {"a": (33, 47), "e": (39,), "g": (44, 60, 72, 76), "R": (12, 16, 25), "S": (53,)},
}
REFINED_LETTERS = "aegRS"


def text_strength(optical_size: float) -> float:
    """Details are strongest in text; display retains a quarter-strength cut."""
    if optical_size <= 24:
        return 1.0 - 0.35 * (optical_size - 9) / 15
    return 0.65 - 0.40 * (optical_size - 24) / 16


def refine_points(char, coordinates, ends, flags, stem, optical_size, italic=False):
    """Return a compatible refined outline, without changing its advance."""
    if tuple(ends) != TOPOLOGY[italic][char]:
        raise ValueError(f"{char}: pinned {'italic' if italic else 'upright'} topology changed: {ends}")
    points = [tuple(point) for point in coordinates]
    original = list(points)
    shear = math.tan(math.radians(10)) if italic else 0.0
    amount = min(18.0, stem * 0.16) * text_strength(optical_size)

    def shift(index, dx=0.0, dy=0.0):
        x, y = points[index]
        # Move in the slanted design frame, not against the italic stem angle.
        points[index] = (x + dx + shear * dy, y + dy)

    if char == "a":
        # The left end of the upper arch faces the top of the lower bowl.
        # Shortening it opens that aperture without changing a's silhouette.
        for index in (16, 17):
            shift(index, dy=amount)
        shift(15, dy=amount * 0.35)
        shift(18, dy=amount * 0.25)
        # Ease only the inner arch-to-stem junction; the outer stem stays put.
        for index in (9, 10):
            shift(index, dx=amount * 0.18)
    elif char == "e":
        inner_end, outer_end = (35, 36) if italic else (33, 34)
        shift(inner_end, dy=-amount)
        shift(outer_end, dy=-amount)
        shift(inner_end - 1, dy=-amount * 0.60)
        shift(outer_end + 1, dy=-amount * 0.45)
        # Keep the crossbar level and the x-height/counter roof unchanged.
    elif char == "g":
        inner_indices = range(10, 23 if italic else 24)
        frame_x = [original[i][0] - shear * original[i][1] for i in inner_indices]
        ys = [original[i][1] for i in inner_indices]
        cx = (min(frame_x) + max(frame_x)) / 2
        cy = original[12][1]  # leftmost on-curve of the lower counter
        rx = max(abs(x - cx) for x in frame_x)
        for index in inner_indices:
            x, y = original[index]
            dx = (x - shear * y - cx) / rx * amount * 0.35
            if y >= cy:
                dy = (y - cy) / max(max(ys) - cy, 1) * amount * 0.50
            else:
                dy = (y - cy) / max(cy - min(ys), 1) * amount * 0.30
            shift(index, dx=dx, dy=dy)
        # Relax the small hard turn in the link, preserving its topology.
        link = 32 if italic else 33
        for index, factor in ((link, 0.30), (link + 1, 0.20), (link + 2, 0.08)):
            shift(index, dy=-amount * factor)
    elif char == "S":
        # Match s's slightly oblique exits, not a rotated or scaled lowercase.
        # Keep the already-smaller upper bowl and all overshoot endpoints.
        cut = stem * 0.045
        upper_outer, upper_inner = (30, 31) if italic else (29, 30)
        shift(4, dy=-cut)
        shift(5, dy=cut)
        shift(3, dy=-cut * 0.5)
        shift(6, dy=cut * 0.5)
        shift(upper_outer, dy=cut)
        shift(upper_inner, dy=-cut)
        shift(upper_outer - 1, dy=cut * 0.5)
        shift(upper_inner + 1, dy=-cut * 0.5)
    elif char == "R":
        # A lightly bowed leg with a less congested root. The original bowl,
        # cap height, baseline endpoints and advance remain authoritative.
        bottom_left, inner_top, outer_top, bottom_right = points[13:17]
        inner_top = (inner_top[0] + stem * 0.08, inner_top[1])
        bend = stem * 0.08
        inner_control = ((bottom_left[0] + inner_top[0]) / 2 - bend,
                         (bottom_left[1] + inner_top[1]) / 2)
        outer_control = ((outer_top[0] + bottom_right[0]) / 2 - bend,
                         (outer_top[1] + bottom_right[1]) / 2)
        leg = [bottom_left, inner_control, inner_top, outer_top, outer_control, bottom_right]
        points = points[:13] + leg + points[17:]
        flags = bytes(flags[:13]) + bytes([1, 0, 1, 1, 0, 1]) + bytes(flags[17:])
        ends = [12, 18, 27]
    return points, list(ends), bytes(flags)


def round_advance_delta(char, old_width, new_width, optical_size):
    """Recover part of the space introduced by the narrower custom capitals.

    Do not remove the whole difference: round-to-round pairs need optical air.
    The adjustment affects each glyph's fitting, not global tracking or bowls.
    """
    text_fraction = {"C": 0.50, "G": 0.60, "O": 0.68, "Q": 0.68, "Ø": 0.68}[char]
    display_fraction = {"C": 0.70, "G": 0.80, "O": 0.82, "Q": 0.82, "Ø": 0.82}[char]
    progress = (optical_size - 9) / 31
    fraction = text_fraction + (display_fraction - text_fraction) * progress
    return (new_width - old_width) * fraction


def tabular_one_points(coordinates, ends, flags, advance, italic=False):
    """A dedicated, single-contour tnum one; never changes proportional one."""
    if list(ends) != [6] or len(coordinates) != 7 or not all(flag & 1 for flag in flags):
        raise ValueError("pinned proportional-one topology changed")
    pts = [tuple(point) for point in coordinates]
    shear = math.tan(math.radians(10)) if italic else 0.0
    left, right = pts[0][0], pts[6][0]
    stem = right - left
    foot_height = stem * 0.74
    foot_width = max(advance * 0.54, stem * 1.80)
    center = (left + right) / 2
    foot_left, foot_right = center - foot_width / 2, center + foot_width / 2
    top_shift = shear * foot_height
    points = [(left + top_shift, foot_height)] + pts[1:6] + [
        (right + top_shift, foot_height),
        (foot_right + top_shift, foot_height),
        (foot_right, 0),
        (foot_left, 0),
        (foot_left + top_shift, foot_height),
    ]
    # Ink-centre the full authored outline, including the italic flag.
    shift = advance / 2 - (min(p[0] for p in points) + max(p[0] for p in points)) / 2
    points = [(x + shift, y) for x, y in points]
    return points, [len(points) - 1], bytes([1] * len(points))
