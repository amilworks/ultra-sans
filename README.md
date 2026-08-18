# Ultra Sans

Ultra Sans is the programmatically drawn typeface for BisQue Ultra. It starts
from DM Sans, then applies measured geometry and OpenType features for dense
scientific interfaces and sustained on-screen reading.

This repository is the font's source of truth. Application CSS, typography
roles, and product integration tests stay in their consuming repositories.

> **Status:** development snapshot. The outlines and artifact hashes are
> reproducible, but the family has not reached a stable public release.

## What is in the current face

- variable roman and italic, `wght` 100–1000 and `opsz` 9–40
- reference-matched `C O G Q Ø` geometry across the full design space
- a narrower, asymmetric lowercase `s` tuned for sentence rhythm at text sizes
- 104 Greek codepoints grafted from Inter and matched at every master
- real tabular figures behind the `tnum` OpenType feature
- a generated slashed zero behind the dormant `zero` feature
- original DM Sans spacing, kerning coverage, vertical metrics, and most outlines

DM Sans Mono informed the small-size `G` clarity check; it is not an outline
donor. This repository currently builds the proportional Ultra Sans family, not
an Ultra Mono family.

## Build and verify

Requirements: `uv` and `curl`.

```bash
uv sync --frozen
make verify
make build
```

`make build` downloads the two pinned DM Sans masters into `.cache/`, verifies
their SHA-256 digests, validates the vendored Inter inputs, rebuilds both WOFF2
files, checks geometry and OpenType invariants, and confirms the committed byte
sizes and digests.

To inspect the type interactively:

```bash
make specimen
```

Then open [http://localhost:5310/specimen/](http://localhost:5310/specimen/).

## Release artifacts

| File | Style | Size | SHA-256 |
| --- | --- | ---: | --- |
| `fonts/UltraSans-Variable.woff2` | Roman | 126,756 bytes | `498bfe2daea07ba012de62f61829273d70be1999cb727c4bb75e48c2a2a4b80d` |
| `fonts/UltraSans-Italic-Variable.woff2` | Italic | 154,544 bytes | `b38f97e13be2018a42afade2321c4a713c72872c7958b763dd065765033988dc` |

Basic web use:

```css
@font-face {
  font-family: "Ultra Sans";
  src: url("./UltraSans-Variable.woff2") format("woff2");
  font-style: normal;
  font-weight: 100 1000;
  font-display: swap;
}

@font-face {
  font-family: "Ultra Sans";
  src: url("./UltraSans-Italic-Variable.woff2") format("woff2");
  font-style: italic;
  font-weight: 100 1000;
  font-display: swap;
}
```

## Repository map

- `font-lab/build_ultra_tabular.py` — adopted, deterministic geometry builder
- `fonts/` — committed release artifacts
- `sources/inter/` — exact Inter 4.1 build inputs
- `specimen/` — interactive small-text and geometry review
- `docs/PROVENANCE.md` — source identity, construction, and artifact evidence
- `font-lab/README.md` — detailed design research and the earlier Inter experiment
- `licenses/` — verbatim upstream SIL Open Font License texts

## License

Ultra Sans is distributed under the SIL Open Font License 1.1. It derives from
DM Sans and incorporates adapted Inter glyphs; both upstream copyright notices
and license texts are preserved under `licenses/`. See [LICENSE.md](LICENSE.md)
and [docs/PROVENANCE.md](docs/PROVENANCE.md) for details.
