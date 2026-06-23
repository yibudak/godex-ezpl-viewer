# Godex EZPL Viewer

Offline, single-file, dot-accurate previewer for **Godex EZPL** label code. Paste the EZPL you send
to the printer and see exactly what it prints (fonts, sizes, barcode and QR placement) before you
waste a roll.

**▶ Live demo:** https://yibudak.github.io/godex-ezpl-viewer/

![viewer](docs/screenshot.png)

Online ZPL/EZPL viewers get fonts, sizes, alignment and QR position wrong, because EZPL has
non-obvious rules: fixed 8/12/24 dots/mm, point-based bitmap fonts, a bottom-left QR anchor, 1-bit
output. This tool implements them from a decompile of Godex's GoLabel and the official manual. Full
command reference: [`docs/EZPL.md`](docs/EZPL.md).

## Use it

1. Open `index.html` (double-click or host it). No install, no network.
2. Pick a sample or paste your EZPL.
3. Set DPI (203/300/600), zoom, and optional 1-bit / grid.
4. For pixel-exact glyphs, load your printer's bitmap ROM or a `.ttf`.
5. For true scale, turn on **real size 1:1** and calibrate against a printed label.

It renders the common commands (`^Q/^QD/^W`, `^L…E`, `At`/`AT`/`ATt` text, `Vt`, `Bt` barcodes,
`W` QR, `Rx` box, `La` line, `Hx` table). QR and the common 1D symbologies are verified by decoding;
rarer ones render as sized placeholders.

## Fonts

The page ships only open fonts (Noto Serif, SIL OFL). For an exact match, load your printer's own
fonts: extract them from firmware you own with
[`tools/extract_godex_fonts.py`](tools/extract_godex_fonts.py), or drop a raw firmware `.bin` into
the page. No proprietary font data lives in this repo.

## License

MIT for the code (see [`LICENSE`](LICENSE)); Noto Serif under the SIL OFL 1.1. "Godex" and "EZPL"
are trademarks of their owner. Independent, unaffiliated interoperability tool.
