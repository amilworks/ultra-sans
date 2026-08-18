# Build inputs

`inter/` contains the exact Inter 4.1 WOFF2 files used as geometry donors. They
are committed because Ultra Sans samples their variable outlines at every
master; the build verifies their SHA-256 digests before use.

DM Sans masters are not committed. The builder downloads them from Google Fonts
into `.cache/sources/` and accepts them only when their pinned digests match
`docs/PROVENANCE.md`.

These files remain under their upstream SIL Open Font License 1.1 terms. See
`licenses/` for the verbatim notices.
