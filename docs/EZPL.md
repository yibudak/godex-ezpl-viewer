# Godex EZPL — practical reference

Notes that make hand-written EZPL match the physical printer. Derived from decompiling Godex's
GoLabel design software and the official *EZPL Programmer's Manual*, and verified by decoding the
generated barcodes/QR. The viewer in this repo implements all of it.

> **The only 100% reference is a physical print.** Use the viewer's "real size 1:1" + ruler to
> calibrate, then trust it.

---

## 1. Coordinate system & units (the #1 source of mismatch)

- Origin is **top-left (0,0)**, X right, Y down. Drawing units are **dots**.
- **mm → dot is a FIXED integer, not 25.4:**

  | Resolution | dots/mm | dots/inch | pt → dot (`×dpi/72`) |
  |-----------|---------|-----------|----------------------|
  | 203 dpi   | **8**   | ~203      | ~2.78 |
  | 300 dpi   | **12**  | 300       | ~4.17 |
  | 600 dpi   | **24**  | 600       | ~8.33 |

  So `1 mm = 8 dots` (203 dpi) or `12 dots` (300 dpi). A viewer using 25.4 drifts ~1.5% and the
  error compounds across the label.

- **Mixed units, on purpose:** only the label setup `^Q` (length) and `^W` (width) are in **mm**
  (the firmware converts them). **Every object's X/Y and size is already in dots.** `^QD` gives the
  length in dots instead of mm.

---

## 2. Label setup (header), then `^L … E`

A job is: setup commands, then `^L` (begin), then objects, then `E` (end & print).

```
^Q50,3        ; label length 50 mm, gap 3 mm   (^Q<len>,<gap> | ^Q<len>,0,<feed> | ^QD<dots>,...)
^W52          ; label width 52 mm
^H10          ; darkness 0..19
^S5           ; speed
^AT / ^AD     ; tear / dispense mode
^C1           ; copies
^R0           ; left reference offset (dots)
~Q+0          ; top reference offset (dots, signed)
^L            ; begin label block
  ...objects...
E             ; end + print
```

---

## 3. Text

### 3.1 Built-in bitmap fonts — `At,x,y,x_mul,y_mul,gap,rot,data`
- `t` = font slot, glued to `A`: **A=6pt B=8pt C=10pt D=12pt E=14pt F=18pt G=24pt H=30pt**,
  `I` = 16×26 mono, `K`=OCR-B, `L`=OCR-A, `Zn` = Asian.
- `x_mul`,`y_mul` are **integer zoom** factors of the fixed cell — *not* points and *not* dots.
  Native cell height ≈ `round(pt × dpi/72)` (e.g. font A ≈ 16 dots at 203 dpi).
- `rot` field: `0/1/2/3` = 0/90/180/270; append `I` for inverse. Code page 850.

### 3.2 Built-in TrueType — `AT,x,y,w,h,g,s,d,m,data`  (downloaded: `ATt,...`)
- `w,h` = width/height in **dots**. `h` is the font's pixel height; **`w==h` ⇒ matches the Windows
  font** at `pt = h × 72 / dpi`. So for 12 pt at 203 dpi use `h = round(12 × 203/72) = 34`.
- `s` = rotation `0..3` + optional style `B`(old) `T`(italic, =oblique) `U`(nderline) + Unicode flag
  `E`(UTF-8) `L`/`H`(UTF-16). `d` = encoding (0=ASCII). `m` = 0 aspect / 1 average-width.

### 3.3 Alignment & spacing
There is **no alignment parameter**. `x,y` is the exact top-left of the text; to center/right-align
you must compute the X offset yourself (measure the rendered width). Inter-character spacing is the
`gap` field (dots).

---

## 4. Anchors (often gets the layout wrong)

| Object | Anchor |
|--------|--------|
| Text (`At`,`AT`,`Vt`), Box (`R`), Line (`L`), Table (`H`) | **top-left** |
| QR (`W`), DataMatrix (`XRB`), PDF417 (`P`), Aztec (`Z`), Maxicode (`M`), Pattern (`Q`) | **bottom-left** — grows **upward** from Y |

The QR bottom-left anchor is the classic surprise: a QR at `y=390` with module size 5 and 33 modules
occupies `y = 225 … 390`, not `390 … 555`.

---

## 5. Barcodes

### 1D — `Bt,x,y,narrow,wide,height,rotation,readable,data`
`t` = type, glued to `B`. Widths in **dots**. `readable` ≠ 0 shows the human-readable line.
Type codes (from the manual): `A/A2/A3/A4`=Code39, `P`=Code93, `Q/Q2`=Code128, `B/C/D`=EAN-8,
`E/F/G`=EAN-13, `H/I/J`=UPC-A, `K/L/M`=UPC-E, `N/N2/T`=I2of5, `O`=Codabar, `Y..Y4`=MSI,
`R/U/1/2`=UCC/EAN-128, `S`=PostNet, `3`=Telepen, `4`=FIM, `7`=Plessey, `X`=HIBC.

### QR — `Wx,y,mode,type,ec,mask,mul,len,rotate` + **data on the next line**
`mode` 1=numeric 2=alphanumeric **3=byte** 4=kanji 5=mixed · `type` 1=Model1 **2=Model2** 3=MicroQR ·
`ec` = `L/M/Q/H` · `mask` 0..7 or **8=auto** · `mul` = module size in **dots** · `rotate` 0..3.
URLs use byte mode; module width = `mul`.

Other 2D: DataMatrix `XRBx,y,enlarge,rot,len`+data, Aztec `Zx,y,...`+data, PDF417 `Px,y,...`,
Maxicode `Mx,y,...`.

---

## 6. Shapes

- **Box:** `Rx,y,x1,y1,lrw,ubw` — top-left `(x,y)`, bottom-right `(x1,y1)`, left/right border `lrw`,
  upper/bottom border `ubw` (all dots).
- **Line / filled rectangle:** `La,x,y,x1,y1` — `a` = `o` (overwrite) / `e` (XOR). Axis-aligned only.
- **Table:** `Hx,y,cols,rows,col_w,row_w,line_w`.
- **Pattern:** `Qx,y,width_bytes,height` + raw bitmap data (bottom-left anchored).

---

## 7. Fonts on the wire vs. on screen

- The printer's **scalable** font (used by `AT`) on recent firmware is the **Noto** family
  (the internal-TTF image loads `~H,TTF,1NotoSerif-Regular,...` etc.). The viewer bundles Noto Serif.
- The **bitmap** fonts (`At` A..H) are resident **16×24 glyph bitmaps** in firmware, stored in a
  Godex-specific character order (not ASCII), zlib-compressed under a `GODEX2GCompress` tag. The
  viewer can render them exactly if you load that ROM (see `tools/extract_godex_fonts.py`).
- The printer is **1-bit** (pure black/white, no antialiasing); enable the viewer's 1-bit mode to see
  the real thermal edges.
