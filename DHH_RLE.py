from __future__ import annotations
import argparse, csv, json, struct
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
from PIL import Image

@dataclass
class GlyphEntry:
    index: int
    codepoint: int
    vertical_offset: int
    advance: int
    data_offset: int

def u32(b: bytes, o: int) -> int: return struct.unpack_from("<I", b, o)[0]
def s32(b: bytes, o: int) -> int: return struct.unpack_from("<i", b, o)[0]
def u16(b: bytes, o: int) -> int: return struct.unpack_from("<H", b, o)[0]

def next_pow2(x: int) -> int:
    if x <= 1: return 1
    return 1 << ((x - 1).bit_length())

def parse_fnt(blob: bytes) -> Tuple[int, int, int, int, List[GlyphEntry]]:
    sc, unk, fs, ls = u32(blob,0), u32(blob,4), u32(blob,8), u32(blob,12)
    glyphs: List[GlyphEntry] = []
    off = 16
    for i in range(sc):
        glyphs.append(GlyphEntry(i, u32(blob,off), s32(blob,off+4), u32(blob,off+8), u32(blob,off+12)))
        off += 16
    return sc, unk, fs, ls, glyphs

def decode_type1(blob: bytes, off: int, next_off: int, swap_bgr: bool) -> Tuple[Image.Image, Dict]:
    w, h = u16(blob, off), u16(blob, off+2)
    ct = u16(blob, off+0x22)
    if ct != 1: raise ValueError(f"Unsupported compression type={ct} at 0x{off:X}")
    s = blob[off+0x24:next_off]
    buf = bytearray(w*h*4)
    def setpx(x: int, y: int, c0: int, c1: int, c2: int):
        a = ((c0<<6)&0xC0) | ((c2&3)<<4) | ((c1&1)<<3)
        if a >= 0xF8: a = 0xFF
        r,g,b = (c2,c1,c0) if swap_bgr else (c0,c1,c2)
        p = (y*w + x)*4
        buf[p:p+4] = bytes((r,g,b,a))
    x=y=i=0
    L = len(s)
    while i < L and y < h:
        b = s[i]; i += 1
        op = b >> 6
        ln = b & 0x1F
        if b & 0x20:
            if i >= L: break
            ln = ln*0x100 + s[i]; i += 1
        if op == 0:
            x += ln
        elif op == 1:
            for _ in range(ln):
                if i+3 > L: break
                c0,c1,c2 = s[i],s[i+1],s[i+2]; i += 3
                if 0 <= x < w and 0 <= y < h: setpx(x,y,c0,c1,c2)
                x += 1
        elif op == 2:
            if i+3 > L: break
            c0,c1,c2 = s[i],s[i+1],s[i+2]; i += 3
            for _ in range(ln):
                if 0 <= x < w and 0 <= y < h: setpx(x,y,c0,c1,c2)
                x += 1
        elif op == 3:
            if ln == 0: break
            y += ln
            x = 0
        if x >= w: x %= w
    return Image.frombytes("RGBA",(w,h),bytes(buf)), {"w":w,"h":h,"compressionType":ct,"stream_len":len(s)}

def alpha_bbox(img: Image.Image) -> Tuple[int,int,int,int]:
    w,h = img.size
    px = img.load()
    x0,y0,x1,y1 = w,h,-1,-1
    for yy in range(h):
        for xx in range(w):
            if px[xx,yy][3]:
                if xx < x0: x0 = xx
                if yy < y0: y0 = yy
                if xx > x1: x1 = xx
                if yy > y1: y1 = yy
    if x1 < x0 or y1 < y0: return (0,0,0,0)
    return (x0,y0,x1+1,y1+1)

def shelf_pack(items: List[Tuple[int,int,int]], max_w: int, pad: int) -> Tuple[Dict[int,Tuple[int,int]], int]:
    x=y=row_h=0
    place: Dict[int,Tuple[int,int]] = {}
    for gid,w,h in items:
        ww,hh = w+2*pad, h+2*pad
        if x + ww > max_w and x > 0:
            y += row_h
            x = 0
            row_h = 0
        place[gid] = (x+pad, y+pad)
        x += ww
        if hh > row_h: row_h = hh
    return place, y + row_h

def main():
    
    print("\n" + "="*60)
    print(" Detective Hayseed - Hollywood - RLE - MADE BY RABATINI")
    print("="*60 + "\n")
    ap = argparse.ArgumentParser()
    ap.add_argument("fnt", type=Path)
    ap.add_argument("-o","--out", type=Path, default=None)
    ap.add_argument("--no-individual", action="store_true")
    ap.add_argument("--no-atlas", action="store_true")
    ap.add_argument("--atlas-width", type=int, default=1024)
    ap.add_argument("--pad", type=int, default=1)
    ap.add_argument("--no-bgr-swap", action="store_true")
    a = ap.parse_args()
    
    blob = a.fnt.read_bytes()
    sc, unk, fs, ls, glyphs = parse_fnt(blob)

    out_dir = a.out if a.out else Path(a.fnt.with_suffix("").name + "_out")
    out_dir.mkdir(parents=True, exist_ok=True)

    glyph_dir = out_dir / "glyphs_png"
    if not a.no_individual: glyph_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    crops = []
    swap_bgr = not a.no_bgr_swap

    for gi,g in enumerate(glyphs):
        next_off = glyphs[gi+1].data_offset if gi+1 < len(glyphs) else len(blob)
        img, meta = decode_type1(blob, g.data_offset, next_off, swap_bgr)
        ow,oh = img.size
        bbox = alpha_bbox(img)
        crop = Image.new("RGBA",(1,1),(0,0,0,0)) if bbox==(0,0,0,0) else img.crop(bbox)

        if not a.no_individual:
            hx = f"{g.codepoint:04X}" if g.codepoint <= 0xFFFF else f"{g.codepoint:06X}"
            img.save(glyph_dir / f"{g.index:03d}_U+{hx}.png")

        try: ch = chr(g.codepoint)
        except Exception: ch = ""
        rows.append({
            "index": g.index, "codepoint": g.codepoint, "char": ch,
            "verticalOffset": g.vertical_offset, "advance": g.advance,
            "glyph_w": ow, "glyph_h": oh,
            "bbox_x0": bbox[0], "bbox_y0": bbox[1], "bbox_x1": bbox[2], "bbox_y1": bbox[3],
            "crop_w": crop.size[0], "crop_h": crop.size[1],
            "dataOffset": g.data_offset, "compressionType": meta["compressionType"], "stream_len": meta["stream_len"],
        })
        crops.append((g.index, g.codepoint, g.advance, bbox, crop, ow, oh))

    with (out_dir/"glyphs.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        if rows:
            w.writeheader()
            w.writerows(rows)

    if not a.no_atlas:
        pad = max(0, a.pad)
        items = [(idx, crop.size[0], crop.size[1]) for (idx,cp,adv,bbox,crop,ow,oh) in crops]
        items.sort(key=lambda t:(-t[2], -t[1], t[0]))
        place, used_h = shelf_pack(items, a.atlas_width, pad)
        ah = next_pow2(used_h)
        atlas = Image.new("RGBA", (a.atlas_width, ah), (0,0,0,0))
        by_idx = {idx:(cp,adv,bbox,crop,ow,oh) for (idx,cp,adv,bbox,crop,ow,oh) in crops}
        m: Dict[str,Dict] = {}
        for idx,(x,y) in place.items():
            cp,adv,bbox,crop,ow,oh = by_idx[idx]
            atlas.paste(crop, (x,y))
            m[str(cp)] = {
                "index": idx, "codepoint": cp,
                "char": chr(cp) if 0 <= cp <= 0x10FFFF else "",
                "x": int(x), "y": int(y), "w": int(crop.size[0]), "h": int(crop.size[1]),
                "bbox_x0": int(bbox[0]), "bbox_y0": int(bbox[1]),
                "advance": int(adv), "orig_w": int(ow), "orig_h": int(oh),
            }
        atlas.save(out_dir/"atlas.png")
        (out_dir/"atlas.json").write_text(json.dumps({
            "source_fnt": a.fnt.name, "symbolCount": sc, "unk": unk, "fontSize": fs, "lineSpacing": ls,
            "atlas": {"w": a.atlas_width, "h": ah, "pad": pad}, "glyphs": m
        }, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
