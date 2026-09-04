# Ultra Sans 0.103 — adopted circular forms

Amil Khan selected **“Study · circular outer contour”** from the 0.102 proof.
This revision adopts that exact upright `O/o` construction, not the intermediate
“rounder” study. It extends the construction to italic, `Q/Ø/ø`, and dependent
accents. [Review the actual-font comparison](../font-lab/circular.html).

## Geometry and scope

Each outer bowl uses sixteen quadratic arc segments, with equal horizontal and
vertical radii. Quadratic curves approximate the circle; integer font-unit
rounding introduces a further small deviation. The inner counter is an ellipse
whose horizontal and vertical dimensions preserve the previous side and top
stroke thicknesses independently. This is **not** a uniform-stroke circular ring.

The construction keeps the previous height and overshoot. At weight 400, optical
size 14, upright O grows from about 635 to 724 units wide (14%); o grows from
496 to 528 units (6%). Width/height is now 1:1 for each outer contour. Advances
grow by the same amount as the bowl, retaining the existing left/right space.
There is no global tracking or font-weight adjustment. Line breaks can change.

Italic is de-sheared into its design frame, constructed there, then sheared back
to the existing ten-degree slope. Its on-screen outline is therefore a slanted
circle, not a literal upright circle imposed on an italic word.

`Q`, `Ø`, and `ø` use circular bowls while their existing tail/slash contours are
translated to the new centre without stretching or thickening. The overlap
flag is retained explicitly. Accent components move by half the width delta;
their advances and variable phantom points follow the base. Sixteen dependent
composites are updated in each style.

**Unchanged:** C/G; approved a/e/g/R/S/s; simple I; question marks; other basic
letters including b/d/p/q; proportional figures; the footed tabular one; Greek;
existing kerning tables and vertical metrics. Ultra’s reading weight remains
400. This is the selected visual direction, not evidence of faster reading.

## Construction

- `font-lab/circular_geometry.py` contains the bounded outline recipe.
- `redraw_circular_bowls` snapshots the fully fitted pre-circle font. It samples
  the twelve existing masters: weights 100/300/400/1000 × optical sizes 9/24/40.
- Compatible contour topology is required before constructing gvar deltas.
- `record_circular_baseline.py` is a maintenance command, not a build dependency.
  Its committed fixture records 0.102 and the original circle study from commit
  `0820c8e2bdeaf23392c50c9ed18aa6e6d3071a82`. Tests use the fixture offline.
- `make proof` generates the new embedded-font comparison. `make proof-0102`
  regenerates the historical comparison, pinned to its original two revisions.
  The archived study is not silently regenerated from the new circular font.

## Verification

`make check` covers exact upright-study outline and advance matching, protected
letters and spacing, stroke contrast, overshoot, diagonal shape preservation,
accent advances, contour winding, positive counters, and circular interpolation
at 88 locations per style. The original Greek, punctuation, tabular-figure,
source-identity, metadata and output-hash checks remain active. Browser review
includes roman and italic, light and dark, desktop and narrow layouts, and
10–18px reading samples. The 10px row is a stress test, not a body-size target.

Authorship and licensing remain unchanged: designed and authored by **Amil
Khan**, PhD student in Electrical and Computer Engineering at UCSB, for **Ultra**,
an agentic system for science. Upstream DM Sans and Inter credits are preserved.
