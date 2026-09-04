# Ultra Sans 0.102 — defining-letter refinements

Designed and authored by **Amil Khan**, PhD student in Electrical and Computer
Engineering at the University of California, Santa Barbara, for **Ultra**, an
agentic system for science. This describes the derivative design; upstream
DM Sans and Inter authorship and licenses remain intact.

## Intent

Refine the reading face without replacing its voice. The approved 0.101 `s`,
question marks, simple capital `I`, base `n/o`, and proportional figures are
protected. Ultra's reading weight remains **400**. These edits are optical
design decisions, not evidence of faster reading; that requires reader tests.
The secondary `r/t/f` pass keeps their existing fitting and terminals: the
proof includes `rn / m`, `rt`, `fr`, `fi`, `fl`, and the `ss/se/st/rs` rhythm.
There is no new mandatory I/l alternate or decorative terminal treatment.

## Implemented geometry

All distances below use the 1000-unit em. The recipe runs independently for
roman and italic at all 12 `wght × opsz` masters. Italic point movements follow
the existing 10° design frame rather than distorting the stem angle.

| Family | Change | Boundary preserved |
| --- | --- | --- |
| `a` | Shorten the downward-facing upper-arch terminal and ease its inner junction | Double-storey form, advance, cap/x-height, outer stem |
| `e` | Lower the lower-right exit to open the mouth, with adjacent controls eased | Level crossbar, counter roof, advance and x-height |
| `g` | Expand the lower counter slightly and relax the link's turn | Two-storey form, ear, outer extents and advance |
| `R` | Replace the straight leg with a very lightly bowed quadratic leg; ease its root | Original bowl, cap height, baseline endpoints and advance |
| `S` | Introduce restrained oblique exit cuts related to the approved `s` | Existing bowl balance, overshoot and advance |
| `O C G Q Ø` | Refit sidebearings/advances to the existing narrower ink | Approved curve/stroke geometry, names and kerning coverage |
| `1.tnum` | Dedicated footed outline, ink-centred within the zero-width cell | Proportional `1`; equal tabular advances and feature opt-in |

### Text details

The aperture amount is `min(18, stem × 0.16) × strength`. Strength is 1 at
opsz 9, 0.65 at 24, and 0.25 at 40, interpolated piecewise. Thus body details
are not exaggerated at display sizes. The `g` counter expands by fractions of
that amount (0.35 horizontally, 0.50 above and 0.30 below its counter centre).
`R` uses an 8%-of-stem control-point/root adjustment; `S` uses 4.5%-of-stem
terminal adjustments. This is not global thinning or letterspacing.

### Round-cap fitting

Recover part, not all, of the old-to-new ink-width difference: C 50–70%,
G 60–80%, and O/Q/Ø 68–82%, progressing from text to display. Move the ink
centre and dependent accents by half the advance delta. Q/Ø use **O's bowl
width change**, not their tail/slash overhangs. Composite sidebearings are
refreshed after the outline changes. Capital-containing line lengths can change;
the upstream GPOS kerning coverage is retained.

### Tabular one

The footer spans at least 54% of the shared digit cell; its height is 74% of
the one stem thickness. The flag and upper stem remain inherited from the
proportional source. A single compatible contour avoids overlapping footer
components and is independently centred at every master. At interpolated
locations the ink extrema can switch points, so exact centring is nonlinear;
the test bound is less than 0.1px at a 16px font size. Default prose figures
are unchanged. Enable the new form with `font-variant-numeric: tabular-nums`.

## Why not perfect circles by default?

At 400/14, a circular outer contour at the existing height widens O's ink by
approximately 14% and o's by 6%. It changes the rhythm of “Open”, “COCO”, and
“noon”, and would invite coordinated changes to C/G and other bowl letters.
That is a new geometric direction, not a free legibility improvement.

The [actual-font comparison](../font-lab/refinements.html) includes the adopted
optical forms, a 45%-toward-circular study, and a circular-outer-contour study.
The studies change **only O/o**, preserve the existing horizontal/vertical
stroke contrast, and use compatible quadratic curves. They are embedded in
the proof, never substituted into the release fonts. A circular outer contour
does not imply a concentric monoline ring: optical stroke correction remains.

## Verification contract

- SHA-pinned DM Sans and Inter inputs; source-aware instance cache.
- Compatible point/contour topology at all 12 masters, separately for each style.
- 88 weight/optical locations per style for interpolated advances, extents,
  tabular fitting, and positive ink area.
- Protected glyph outlines compared against 0.101 golden fixtures at eight
  locations per style, including the simple I, s, ?/¿ and proportional digits.
- Accented composite advances checked against their base-letter adjustments.
- Existing Greek, slashed-zero, question-mark, round-stroke, overshoot,
  metadata and OpenType checks retained.
- Byte-size/SHA-256 pins, deterministic rebuild, and browser proof using the
  actual WOFF2 files, including true italic and 10/12px stress samples.

The 10px sample is a stress test, not a body-text recommendation. Browser
screenshots establish rendering and layout, not reading-speed gains.

### Completed local validation — 2026-09-04

`make check` passed all eight regression tests, the existing font checks, and
the regenerated light/dark README hero checks. A second complete build produced
the same pinned bytes for both styles. HarfBuzz shaping confirmed inherited
`fi/fl` ligatures and kerning, dedicated `one.tnum`, equal tabular advances,
and combined `tnum` + `zero` behavior.

The six proof font faces loaded in Chromium. Desktop light/dark proofs and a
390px-wide proof had no horizontal page overflow; regular, medium/bold and
extreme-weight samples were inspected. Ultra's local frontend build,
source/production typography contracts, and bundle budgets passed. The local
conversation rendered with the custom Ultra Sans face at 16px/400 and automatic
optical sizing. Windows rasterization and human reading-speed/comprehension
testing have not been performed in this pass.
