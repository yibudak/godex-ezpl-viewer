#!/usr/bin/env python3
"""
extract_godex_fonts.py — pull the real fonts out of Godex printer firmware you already own.

Godex firmware packages ("DownloadTool" .zip files) contain .BIN images that embed:

  1. A zlib-compressed bitmap-font ROM, tagged  `GODEX2GCompress,<decompressed_size>\\n` then a
     zlib stream (78 9c ...). This holds the resident A..H bitmap fonts (16-wide cells, custom
     character order). Load the *decompressed* output in the viewer's "Bitmap ROM" box for
     pixel-exact `At` glyphs.

  2. An "internal TTF" image: a sequence of  `~H,TTF,<reg><name>,<size>\\r<raw TTF bytes>` blocks.
     These are the scalable fonts (Noto family on recent firmware). The Latin one can be loaded
     as the viewer's "AT font".

Usage:
    python extract_godex_fonts.py <file-or-folder> [-o OUTDIR]

It scans the given .bin (or every *.bin/*.BIN under a folder) and writes whatever it finds to OUTDIR
(default ./godex_fonts_out). Interoperability tool — reads firmware you own; don't redistribute the
extracted proprietary fonts.
"""
import sys, os, re, zlib, argparse, glob

def find_bitmap_rom(data):
    """Return decompressed bitmap-font ROM bytes, or None."""
    p = data.find(b"GODEX2GCompress,")
    if p < 0:
        return None
    nl = data.find(b"\n", p)
    try:
        declared = int(data[p:nl].split(b",")[1])
    except Exception:
        declared = None
    z = data.find(b"\x78\x9c", p)          # zlib header
    if z < 0:
        return None
    try:
        rom = zlib.decompress(data[z:])
    except zlib.error:
        d = zlib.decompressobj()
        rom = d.decompress(data[z:])
    if declared and len(rom) != declared:
        print(f"  note: decompressed {len(rom)} bytes (header said {declared})")
    return rom

def find_ttfs(data):
    """Yield (register, name, ttf_bytes) for each ~H,TTF,... block. Header ends with a single \\r."""
    i = 0
    while True:
        h = data.find(b"~H,TTF,", i)
        if h < 0:
            break
        cr = data.find(b"\r", h)
        if cr < 0:
            break
        try:
            hdr = data[h + 7:cr].decode("latin1")     # "<reg><name>,<size>"
            reg = hdr[0]
            name, size = hdr[1:].rsplit(",", 1)
            size = int(size)
        except Exception:
            i = cr + 1
            continue
        start = cr + 1
        blob = data[start:start + size]
        if blob[:4] in (b"\x00\x01\x00\x00", b"OTTO", b"true", b"ttcf"):
            yield reg, name, blob
        i = start + size

def process(path, outdir):
    with open(path, "rb") as f:
        data = f.read()
    base = os.path.splitext(os.path.basename(path))[0]
    found = False

    rom = find_bitmap_rom(data)
    if rom:
        out = os.path.join(outdir, base + ".bitmap_rom.bin")
        with open(out, "wb") as f:
            f.write(rom)
        print(f"  bitmap-font ROM  -> {out}  ({len(rom)} bytes)  [load this in 'Bitmap ROM']")
        found = True

    for reg, name, blob in find_ttfs(data):
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", name) or ("font" + reg)
        out = os.path.join(outdir, f"{base}.ttf_{reg}_{safe}.ttf")
        with open(out, "wb") as f:
            f.write(blob)
        print(f"  TTF reg '{reg}': {name}  -> {out}  ({len(blob)} bytes)")
        found = True

    if not found:
        print("  (no Godex font data found in this file)")

def main():
    ap = argparse.ArgumentParser(description="Extract fonts from Godex firmware .bin files.")
    ap.add_argument("input", help="a .bin file, or a folder to scan")
    ap.add_argument("-o", "--outdir", default="godex_fonts_out")
    a = ap.parse_args()

    if os.path.isdir(a.input):
        files = sorted(glob.glob(os.path.join(a.input, "**", "*.bin"), recursive=True) +
                       glob.glob(os.path.join(a.input, "**", "*.BIN"), recursive=True))
    else:
        files = [a.input]
    if not files:
        print("No .bin files found.")
        return 1

    os.makedirs(a.outdir, exist_ok=True)
    for p in files:
        print(f"{p}:")
        try:
            process(p, a.outdir)
        except Exception as e:
            print(f"  error: {e}")
    print(f"\nDone. Output in: {a.outdir}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
