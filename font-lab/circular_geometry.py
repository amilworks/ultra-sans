"""The approved O/o circle study, extended to related bowls and true italic.

The outer contour is a 16-segment quadratic approximation of a circle. The
counter is independently sized: preserving side/top stroke contrast matters
more than making a mathematically uniform ring. Geometry lives in the upright
design frame; italic is sheared back to DM Sans's existing ten-degree slope.
"""
import math

CIRCULAR_LETTERS = "OoQØø"
ITALIC_SHEAR = math.tan(math.radians(10))
RING_INDICES = {"O": (0, 1), "o": (0, 1), "Q": (1, 2), "Ø": (0, 1), "ø": (1, 2)}


def ellipse(cx, cy, rx, ry, clockwise):
    """Same points as the selected circular-outer-contour study."""
    points, flags = [], []
    step = (-1 if clockwise else 1) * math.tau / 16
    for index in range(16):
        angle = step * index
        points.append((cx + rx * math.cos(angle), cy + ry * math.sin(angle)))
        flags.append(1)
        midpoint = angle + step / 2
        correction = 1 / math.cos(step / 2)
        points.append((cx + rx * math.cos(midpoint) * correction, cy + ry * math.sin(midpoint) * correction))
        flags.append(0)
    return points, flags


def split_contours(coords, ends, flags, italic=False):
    shear = ITALIC_SHEAR if italic else 0
    contours, start = [], 0
    for end in ends:
        contours.append(([(x - shear * y, y) for x, y in coords[start:end + 1]], [flag & 1 for flag in flags[start:end + 1]]))
        start = end + 1
    if start != len(coords):
        raise ValueError("contour endpoints do not cover the outline")
    return contours


def box(points):
    return min(x for x, _ in points), min(y for _, y in points), max(x for x, _ in points), max(y for _, y in points)


def circular_points(char, coords, ends, flags, italic=False, fraction=1.0):
    """Return compatible points, ends, flags, and the advance-width delta.

    Preserve left/right side-space in the design frame. Translate (never
    scale/thicken) the existing Q tail and Ø/ø slash to the new bowl centre.
    The fraction argument exists only for the archived 45% shape study.
    """
    if char not in RING_INDICES or len(ends) != (2 if char in "Oo" else 3):
        raise ValueError(f"unsupported circular outline: {char}")
    contours = split_contours(coords, ends, flags, italic)
    indices = RING_INDICES[char]
    rings = [contours[index][0] for index in indices]
    if any(len(points) < 16 for points in rings):
        raise ValueError(f"unexpected bowl topology: {char}")
    outer, inner = sorted((box(points) for points in rings), key=lambda b: (b[2] - b[0]) * (b[3] - b[1]), reverse=True)
    old_width, height = outer[2] - outer[0], outer[3] - outer[1]
    width = old_width + fraction * (height - old_width)
    side_stroke = (old_width - (inner[2] - inner[0])) / 2
    top_stroke = (height - (inner[3] - inner[1])) / 2
    if not (0 < side_stroke < width / 2 and 0 < top_stroke < height / 2):
        raise ValueError(f"collapsed counter: {char}")
    delta = width - old_width
    cx, cy = outer[0] + width / 2, (outer[1] + outer[3]) / 2
    outside, outer_flags = ellipse(cx, cy, width / 2, height / 2, True)
    inside, inner_flags = ellipse(cx, cy, width / 2 - side_stroke, height / 2 - top_stroke, False)
    points, new_flags, new_ends = outside + inside, outer_flags + inner_flags, [31, 63]
    for index, (extra, extra_flags) in enumerate(contours):
        if index in indices:
            continue
        points.extend((x + delta / 2, y) for x, y in extra)
        new_flags.extend(extra_flags)
        new_ends.append(len(points) - 1)
        new_flags[0] |= 0x40  # OVERLAP_SIMPLE: the original diagonal crosses the bowl.
    shear = ITALIC_SHEAR if italic else 0
    return [(x + shear * y, y) for x, y in points], new_ends, bytes(new_flags), delta
