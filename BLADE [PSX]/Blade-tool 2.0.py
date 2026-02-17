#-----------BLADE [PSX] Made by Rabatini aka Luke------------#
"""
Combined Blade PSX Tools
Includes: RLE Compressor/Decompressor, SNDVRAM DAT Unpack/Pack,
Image Split/Merge, Blade Common.dat Unpack/Pack, LevelBin Extract/Insert
thanks Mummrar for Rle DELPHI CODE
"""

import os
import struct
import sys
import re
import argparse
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from collections import OrderedDict


# -------------------- Shared I/O --------------------
def read_file(path, mode="rb"):
    with open(path, mode) as f:
        return f.read()

def write_file(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)

# -------------------- RLE Compressor/Decompressor --------------------
def rle_decompress(src: bytes) -> bytes:
    out, i, n = bytearray(), 0, len(src)
    while i < n:
        flag = src[i]; i += 1
        if flag & 0x80:
            cnt = ((~flag) & 0xFF) + 2
            out.extend([src[i]] * cnt); i += 1
        else:
            cnt = min(flag + 1, n - i)
            out.extend(src[i:i+cnt]); i += cnt
    return bytes(out)

def rle_compress(src: bytes) -> bytes:
    out, i, n = bytearray(), 0, len(src)
    while i < n:
        rb, j = src[i], i + 1
        while j < n and src[j] == rb and (j - i) < 0x7F + 2:
            j += 1
        run = j - i
        if run >= 3:
            out += bytes([(~(run - 2)) & 0xFF, rb]); i += run
        else:
            start = i; i += 1
            while i < n and not(i+2 < n and src[i] == src[i+1] == src[i+2]) and (i - start) < 0x7F:
                i += 1
            lit = i - start
            out.append((lit - 1) & 0x7F)
            out.extend(src[start:i])
    return bytes(out)

class RLEFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=15)
        ttk.Label(self, text="RLE Compressor / Decompressor",
                  font=("Helvetica", 16, "bold")).pack(pady=(0,12))
        ttk.Button(self, text="Decompress file…", command=self.decomp)\
            .pack(fill="x", pady=4)
        ttk.Button(self, text="Compress file…",   command=self.comp)\
            .pack(fill="x", pady=4)

    def _io(self, func, suffix):
        src = filedialog.askopenfilename(title="Select file", filetypes=[("All", "*.*")])
        if not src: return
        try:
            out = func(read_file(src))
            base,_ = os.path.splitext(os.path.basename(src))
            dst = filedialog.asksaveasfilename(
                title="Save as", defaultextension=".bin",
                initialfile=f"{base}_{suffix}.bin")
            if dst:
                write_file(dst, out)
                messagebox.showinfo("Done", dst)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def decomp(self): self._io(rle_decompress, "dec")
    def comp  (self): self._io(rle_compress,   "cmp")

# -------------------- SNDVRAM DAT Unpack/Pack --------------------
def snd_parse(data: bytes):
    tex_off, snd_off, decl = struct.unpack_from("<III", data, 0)
    region = snd_off - tex_off
    ptrs, tbl, prev, pos = [], [], -1, tex_off + 4
    while pos + 4 <= snd_off:
        rel = struct.unpack_from("<I", data, pos)[0]
        if rel <= prev or rel >= region: break
        ptrs.append(tex_off + rel); tbl.append(pos)
        prev, pos = rel, pos + 8
    sizes = [(ptrs[i+1] if i+1 < len(ptrs) else snd_off) - p
             for i,p in enumerate(ptrs)]
    return tex_off, snd_off, decl, ptrs, tbl, sizes

class SNDVFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=15)
        ttk.Label(self, text="SNDVRAM.DAT Tool", font=("Helvetica", 16, "bold"))\
            .pack(pady=(0,12))
        ttk.Button(self, text="Unpack DAT…", command=self.unpack).pack(fill="x", pady=4)
        ttk.Button(self, text="Pack DAT…",   command=self.pack  ).pack(fill="x", pady=4)

    def unpack(self):
        src = filedialog.askopenfilename(
            title="Select SNDVRAM.DAT", filetypes=[("DAT", "*.DAT"), ("All", "*.*")]
        )
        if not src: return
        try:
            data = read_file(src)
            tex_off, snd_off, decl, ptrs, _, sizes = snd_parse(data)
        except:
            return messagebox.showerror("Error", "Invalid DAT.")

        out_dir = filedialog.askdirectory(title="Output directory")
        if not out_dir: return
        tdir = os.path.join(out_dir, "textures"); os.makedirs(tdir, exist_ok=True)
        for i,(p,s) in enumerate(zip(ptrs, sizes)):
            write_file(os.path.join(tdir, f"file{i:08d}.bin"), data[p:p+s])
        sdir = os.path.join(out_dir, "sounds"); os.makedirs(sdir, exist_ok=True)
        write_file(os.path.join(sdir, "audio_data.bin"), data[snd_off:decl])
        messagebox.showinfo(
            "Unpack done",
            f"{len(ptrs)} textures extracted\n1 audio file extracted."
        )

    def pack(self):
        src = filedialog.askopenfilename(
            title="Original SNDVRAM.DAT",
            filetypes=[("DAT", "*.DAT"), ("All", "*.*")]
        )
        if not src: return
        tex_dir = filedialog.askdirectory(title="Textures directory")
        if not tex_dir: return
        snd_bin = filedialog.askopenfilename(
            title="audio_data.bin",
            filetypes=[("BIN", "*.bin"), ("All", "*.*")]
        )
        if not snd_bin: return

        try:
            orig = read_file(src)
            tex_off, _, _, ptrs, tbl, orig_sz = snd_parse(orig)
        except:
            return messagebox.showerror("Error", "Invalid DAT.")

        files = sorted(os.listdir(tex_dir))
        if len(files) > len(ptrs):
            messagebox.showwarning("Aviso", "Arquivos extras serão ignorados.")

        blobs = []
        for i in range(len(ptrs)):
            if i < len(files):
                blobs.append(read_file(os.path.join(tex_dir, files[i])))
            else:
                blobs.append(orig[ptrs[i]:ptrs[i]+orig_sz[i]])
        sizes = [len(b) for b in blobs]

        abs_ptrs = [ptrs[0]]
        for i in range(1, len(ptrs)):
            abs_ptrs.append(abs_ptrs[i-1] + sizes[i-1])
        new_snd_off = abs_ptrs[-1] + sizes[-1]

        out = bytearray(orig[:ptrs[0]])
        for b in blobs: out.extend(b)
        out.extend(read_file(snd_bin))
        struct.pack_into("<III", out, 0, tex_off, new_snd_off, len(out))
        for dst,pos in zip(abs_ptrs, tbl):
            struct.pack_into("<I", out, pos, dst - tex_off)

        save = filedialog.asksaveasfilename(
            title="Save packed DAT", defaultextension=".DAT",
            initialfile="SNDVRAM_packed.DAT", filetypes=[("DAT", "*.DAT"), ("All", "*.*")]
        )
        if save:
            write_file(save, out)
            messagebox.showinfo("Pack done", save)

# -------------------- Image Split/Merge Tool (PNG/BMP) --------------------
try:
    from PIL import Image
except ImportError:
    Image = None

def merge_images(paths, save_path):
    if Image is None:
        raise RuntimeError("Pillow not installed.")
    if len(paths) != 4:
        raise ValueError("Selecione exatamente 4 imagens.")
    imgs = [Image.open(p) for p in paths]
    w,h = imgs[0].size
    if any(im.size != (w,h) for im in imgs):
        raise ValueError("Different sizes.")
    out = Image.new("RGBA", (w*2, h*2))
    for im,pos in zip(imgs, [(0,0),(w,0),(0,h),(w,h)]):
        out.paste(im, pos)
    out.save(save_path)

def split_image(path, out_dir):
    if Image is None:
        raise RuntimeError("Pillow not installed.")
    im = Image.open(path)
    w,h = im.size; w2,h2 = w//2, h//2
    boxes = [(0,0,w2,h2),(w2,0,w,h2),(0,h2,w2,h),(w2,h2,w,h)]
    base,ext = os.path.splitext(os.path.basename(path))
    for i,b in enumerate(boxes):
        im.crop(b).save(os.path.join(out_dir, f"{base}_part{i}{ext}"))

class ImgFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=15)
        ttk.Label(self, text="Split/Merge 4 image Tool (PNG/BMP)",
                  font=("Helvetica", 16, "bold")).pack(pady=(0,12))
        ttk.Button(self, text="Merge 4 images…", command=self.merge)\
            .pack(fill="x", pady=4)
        ttk.Button(self, text="Split combined image…", command=self.split)\
            .pack(fill="x", pady=4)

    def merge(self):
        paths = filedialog.askopenfilenames(
            title="Select 4 images", filetypes=[("Images","*.png *.bmp")]
        )
        if not paths: return
        if len(paths)!=4:
            return messagebox.showerror("Error","Select exactly 4 files.")
        dst = filedialog.asksaveasfilename(
            title="Save combined image", filetypes=[("PNG","*.png"),("BMP","*.bmp")],
            defaultextension=".png", initialfile="combined.png"
        )
        if not dst: return
        try:
            merge_images(paths, dst)
            messagebox.showinfo("Done", dst)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def split(self):
        src = filedialog.askopenfilename(
            title="Select combined image", filetypes=[("Images","*.png *.bmp")]
        )
        if not src: return
        out_dir = filedialog.askdirectory(title="Output directory")
        if not out_dir: return
        try:
            split_image(src,out_dir)
            messagebox.showinfo("Done", f"Parts saved in:\n{out_dir}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

# -------------------- Blade Common.dat Unpack/Pack --------------------
ENTRY_SIZE = 16  # 12 name + 4 offset

def pad_name(name: str) -> bytes:
    return name.encode("ascii","ignore")[:12].ljust(12, b"\x00")

class CommonFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=20)
        ttk.Label(self, text="Blade Common.dat Unpack / Pack",
                  font=("Arial", 16, "bold")).pack(pady=(0,14))
        ttk.Button(self, text="🗂  Unpack DAT", command=self.unpack_dat).pack(fill="x", ipady=6, pady=(0,10))
        ttk.Button(self, text="📦  Pack DAT",   command=self.pack_dat).pack(fill="x", ipady=6)

    def parse_header(self, blob: bytes):
        names, offs, p, sz = [], [], 0, len(blob)
        while p + ENTRY_SIZE <= sz:
            n_bytes = blob[p:p+12]; off = struct.unpack_from("<I", blob, p+12)[0]
            if not any(n_bytes): break
            name = n_bytes.split(b"\x00",1)[0].decode("ascii","ignore").strip()
            names.append(name); offs.append(off); p += ENTRY_SIZE
            if len(offs)>1 and offs[-1]<=offs[-2]:
                raise ValueError("Offsets out of order.")
        if not offs: raise ValueError("No entries found.")
        if min(offs)<p: raise ValueError("Offset inside header.")
        return names, offs

    def unpack_dat(self):
        path = filedialog.askopenfilename(title="Select Common.dat")
        if not path: return
        try:
            blob = read_file(path); names, offs = self.parse_header(blob)
        except Exception as e:
            return messagebox.showerror("Error", f"Parse failed: {e}")
        out_dir = os.path.join(os.path.dirname(path),
                               f"{os.path.splitext(os.path.basename(path))[0]}_extracted")
        os.makedirs(out_dir, exist_ok=True)
        for i, (name,start) in enumerate(zip(names,offs)):
            end = offs[i+1] if i+1<len(offs) else len(blob)
            data = blob[start:end]
            fname = name or f"file_{i:03d}.bin"
            final = os.path.join(out_dir, fname)
            if os.path.exists(final):
                r, e = os.path.splitext(fname)
                final = os.path.join(out_dir, f"{r}_{i}{e}")
            write_file(final,data)
        messagebox.showinfo("Done", f"{len(offs)} files extracted to\n{out_dir}")

    def pack_dat(self):
        base = filedialog.askopenfilename(title="Select original Common.dat")
        if not base: return
        folder = filedialog.askdirectory(title="Select folder with modified files")
        if not folder: return
        save_path = filedialog.asksaveasfilename(defaultextension=".dat", filetypes=[("DAT","*.dat")])
        if not save_path: return
        try:
            names, _ = self.parse_header(read_file(base))
        except Exception as e:
            return messagebox.showerror("Error", f"Base parse failed: {e}")
        file_data, missing = [], []
        for n in names:
            fp = os.path.join(folder, n)
            if os.path.isfile(fp): file_data.append(read_file(fp))
            else: missing.append(n); file_data.append(b"")
        if missing and not messagebox.askyesno("Missing files", "Missing:\n"+ "\n".join(missing)):
            return
        header_len = (len(names)+1)*ENTRY_SIZE
        offs, cursor = [], header_len
        for d in file_data:
            offs.append(cursor); cursor+=len(d)
        final_size=cursor
        header=bytearray()
        for n,o in zip(names,offs):
            header += pad_name(n)+struct.pack("<I",o)
        header += b"\x00"*12+struct.pack("<I",final_size)
        with open(save_path,"wb") as out:
            out.write(header)
            for d in file_data: out.write(d)
        messagebox.showinfo("Done", f"Saved {os.path.basename(save_path)}")

# ---------- constantes ----------
PTR_END_MARK   = 0xFFFFFF00
ENCODING       = "cp1252"
ASCII_MARKER   = 0x18
ASCII_FALLBACK = 0x14

u32 = lambda b, o: struct.unpack_from('<I', b, o)[0]

# ---------- TBL support ----------
def load_tbl(tbl_path: str) -> dict:
    """Lê um arquivo .tbl com linhas 'XX=caractere' (hex byte = char)."""
    mapping = {}
    with open(tbl_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('=', 1)
            try:
                key = int(parts[0], 16)
                val = parts[1]
                mapping[key] = val
            except Exception:
                continue
    return mapping

# auto–load blade.tbl se existir na mesma pasta do .py
SCRIPT_DIR = Path(__file__).resolve().parent
TBL_FILE   = SCRIPT_DIR / 'blade.tbl'
GLOBAL_TBL = load_tbl(str(TBL_FILE)) if TBL_FILE.exists() else None

# ---------- funções base ----------
def get_ascii_start(data: bytes) -> int:
    prev = data[ASCII_MARKER-1]
    return ASCII_MARKER if prev == 0x00 else ASCII_FALLBACK

def detect_ptr_table_offset(data: bytes, block_end: int, ascii_start: int) -> int:
    start = ((block_end + 3) // 4) * 4
    limit = len(data) - 12
    for off in range(start, limit, 4):
        v1 = u32(data, off); v2 = u32(data, off+4); v3 = u32(data, off+8)
        if ascii_start <= v1 < block_end and ascii_start <= v2 < block_end and ascii_start <= v3 < block_end:
            return off
    raise ValueError("Offset de tabela não detectado.")

def index_strings(data: bytes, search_limit: int, ascii_start: int, tbl_map: dict = None):
    """Mapeia strings e offsets. Usa tbl_map ou GLOBAL_TBL se fornecido."""
    tbl = tbl_map or GLOBAL_TBL
    dct, valid = {}, set()
    pos = ascii_start
    while pos < search_limit:
        try:
            end = data.index(b'\x00', pos, search_limit)
        except ValueError:
            break
        raw = data[pos:end]
        if tbl:
            # exceto 0x20, mapear espaço direto do ASCII
            txt = ''.join((chr(b) if b == 0x20 else tbl.get(b, chr(b))) for b in raw)
        else:
            try:
                txt = raw.decode(ENCODING, 'strict')
            except UnicodeDecodeError:
                txt = raw.decode(ENCODING, 'replace')
        dct[pos] = txt
        valid.add(pos)
        pos = end + 1
    return dct, valid

def read_pointer_table(data: bytes, start_offset: int):
    pos, positions, values = start_offset, [], []
    limit = len(data)
    while pos + 4 <= limit:
        val = u32(data, pos)
        if val == PTR_END_MARK:
            break
        positions.append(pos); values.append(val); pos += 4
    ptr_end = pos + 4 if pos + 4 <= limit and u32(data, pos) == PTR_END_MARK else pos
    ptr_end = min(ptr_end, limit)
    return positions, values, ptr_end

def extract_dialogues(data: bytes, block_end: int, ptr_off: int, ascii_start: int, tbl_map: dict = None):
    tbl = tbl_map or GLOBAL_TBL
    strings, valid = index_strings(data, block_end, ascii_start, tbl)
    ptr_pos, ptr_vals, _ = read_pointer_table(data, ptr_off)
    dialogues, used, count = OrderedDict(), set(), 0
    for i in range(len(ptr_vals) - 1):
        if i in used:
            continue
        s, l1 = ptr_vals[i], ptr_vals[i+1]
        if s in valid and l1 in valid:
            count += 1
            speaker = strings[s]
            lines = [(l1, strings[l1])]
            used.update({i, i+1})
            k = i + 2
            while k < len(ptr_vals) and ptr_vals[k] in valid:
                lines.append((ptr_vals[k], strings[ptr_vals[k]]))
                used.add(k)
                k += 1
            dialogues[f'Dialogue {count} | {speaker}'] = lines
    return dialogues

def extract_to_txt(bin_path: str, txt_path: str, tbl_map: dict = None):
    tbl = tbl_map or GLOBAL_TBL
    data = Path(bin_path).read_bytes()
    ascii_start = get_ascii_start(data)
    marker = struct.pack('<I', PTR_END_MARK)
    m_off = data.find(marker, ascii_start)
    if m_off < 0:
        raise ValueError(f"Marcador 0x{PTR_END_MARK:08X} não encontrado.")
    block_end = m_off + 4
    ptr_off = detect_ptr_table_offset(data, block_end, ascii_start)
    dialogues = extract_dialogues(data, block_end, ptr_off, ascii_start, tbl)
    with open(txt_path, 'w', encoding='utf-8') as out:
        out.write(f"# ASCII start @ 0x{ascii_start:08X}\n")
        out.write(f"# Block end  @ 0x{block_end:08X}\n")
        out.write(f"# Pointer tbl @ 0x{ptr_off:08X}\n\n")
        for title, lines in dialogues.items():
            out.write(f'[{title}]\n')
            for off, txt in lines:
                out.write(f'0x{off:08X} | {txt}\n')
            out.write('\n')

def insert_from_txt(bin_path: str, txt_path: str, out_path: str, tbl_map: dict = None):
    tbl = tbl_map or GLOBAL_TBL
    data = Path(bin_path).read_bytes()
    ascii_start = get_ascii_start(data)
    marker = struct.pack('<I', PTR_END_MARK)
    m_off = data.find(marker, ascii_start)
    if m_off < 0:
        raise ValueError(f"Marcador 0x{PTR_END_MARK:08X} não encontrado.")
    block_end = m_off + 4
    ptr_off = detect_ptr_table_offset(data, block_end, ascii_start)
    ptr_pos, ptr_vals, ptr_end = read_pointer_table(data, ptr_off)
    strings_orig, valid_orig = index_strings(data, block_end, ascii_start, tbl)
    edits, rx = {}, re.compile(r'0x([0-9A-Fa-f]+)\s*\|\s*(.*)')
    with open(txt_path, 'r', encoding='utf-8') as f:
        for ln in f:
            if ln.startswith('#') or ln.startswith('[') or not ln.strip():
                continue
            m = rx.match(ln.rstrip('\n'))
            if not m:
                raise ValueError(f"Invalid line: {ln.strip()}")
            off = int(m.group(1), 16)
            if off not in valid_orig:
                raise ValueError(f"Offset 0x{off:08X} fora do bloco.")
            edits[off] = m.group(2)

    # Reconstrói strings atualizadas
    rebuilt, offset_map, cur = bytearray(), {}, ascii_start
    for off in sorted(valid_orig):
        rebuilt.extend(data[cur:min(off, block_end)])
        if off in edits:
            if tbl:
                rev = {v: k for k, v in tbl.items()}
                newb = bytearray()
                for ch in edits[off]:
                    if ch == ' ':
                        newb.append(0x20)
                    else:
                        newb.append(rev.get(ch, ch.encode(ENCODING, 'replace')[0]))
                newb.append(0)
            else:
                newb = edits[off].encode(ENCODING, 'replace') + b'\x00'
            try:
                orig_end = data.index(b'\x00', off, block_end)
                orig_len = orig_end - off + 1
            except ValueError:
                orig_len = block_end - off
        else:
            try:
                orig_end = data.index(b'\x00', off, block_end)
                newb = data[off:orig_end+1]; orig_len = len(newb)
            except ValueError:
                newb = data[off:block_end]; orig_len = len(newb)
        offset_map[off] = ascii_start + len(rebuilt)
        rebuilt.extend(newb)
        cur = off + orig_len

    rebuilt.extend(data[cur:block_end])
    need = block_end - ascii_start
    if len(rebuilt) > need:
        raise ValueError("Strings overflow block.")
    rebuilt.extend(b'\x00' * (need - len(rebuilt)))
    # reescreve sentinel
    sentinel_rel = m_off - ascii_start
    rebuilt[sentinel_rel:sentinel_rel+4] = struct.pack('<I', PTR_END_MARK)

    # atualiza ponteiros
    orig_ptr = data[ptr_off:ptr_end]
    new_ptr = bytearray()
    c, size = 0, len(orig_ptr)
    while c < size:
        abs_off = ptr_off + c
        if abs_off in ptr_pos:
            idx = ptr_pos.index(abs_off)
            val = ptr_vals[idx]
            new_ptr.extend(struct.pack('<I', offset_map.get(val, val)))
            c += 4
            continue
        v = struct.unpack_from('<I', orig_ptr, c)[0]
        if v == PTR_END_MARK:
            new_ptr.extend(struct.pack('<I', PTR_END_MARK))
            c += 4
            continue
        new_ptr.append(orig_ptr[c])
        c += 1
    if len(new_ptr) != size:
        raise ValueError("Pointer block error.")

    # monta e grava o arquivo final
    final = bytearray()
    final.extend(data[:ascii_start])
    final.extend(rebuilt)
    final.extend(data[block_end:ptr_off])
    final.extend(new_ptr)
    final.extend(data[ptr_end:])
    Path(out_path).write_bytes(final)

class LevelFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self.bin_path=None; self.txt_path=None
        subnb = ttk.Notebook(self); subnb.pack(expand=True, fill='both', padx=10, pady=10)
        # Extract tab
        ext = ttk.Frame(subnb, padding=10); subnb.add(ext, text="Extract")
        ttk.Label(ext, text='Extract dialogues from BIN', font=('Segoe UI',12,'underline')).pack(pady=(0,10))
        ttk.Button(ext, text='Select BIN File', command=self.pick_bin_extract).pack(fill='x', pady=5)
        self.lbl_bin_extract = ttk.Label(ext, text='No BIN selected', font=('Segoe UI',10), foreground='gray')
        self.lbl_bin_extract.pack(fill='x', pady=(0,10))
        ttk.Button(ext, text='Export to TXT', command=self.run_extract).pack(fill='x', pady=5)
        # Insert tab
        ins = ttk.Frame(subnb, padding=10); subnb.add(ins, text="Insert")
        ttk.Label(ins, text='Insert edited TXT into BIN', font=('Segoe UI',12,'underline')).pack(pady=(0,10))
        ttk.Button(ins, text='Select Original BIN', command=self.pick_bin_insert).pack(fill='x', pady=5)
        self.lbl_bin_insert = ttk.Label(ins, text='No BIN selected', font=('Segoe UI',10), foreground='gray')
        self.lbl_bin_insert.pack(fill='x', pady=(0,10))
        ttk.Button(ins, text='Select Edited TXT', command=self.pick_txt_insert).pack(fill='x', pady=5)
        self.lbl_txt_insert = ttk.Label(ins, text='No TXT selected', font=('Segoe UI',10), foreground='gray')
        self.lbl_txt_insert.pack(fill='x', pady=(0,10))
        ttk.Button(ins, text='Generate New BIN', command=self.run_insert).pack(fill='x', pady=5)

    def pick_bin_extract(self):
        p = filedialog.askopenfilename(title="Select BIN", filetypes=[("BIN","*.bin"),("All","*.*")])
        if p:
            self.bin_path = p
            self.lbl_bin_extract.config(text=Path(p).name, foreground='black')

    def run_extract(self):
        if not self.bin_path:
            messagebox.showerror("Error", "Please select a BIN file first.")
            return
        dst = filedialog.asksaveasfilename(defaultextension=".txt", title="Save TXT", filetypes=[("TXT","*.txt")])
        if dst:
            try:
                extract_to_txt(self.bin_path, dst)
                messagebox.showinfo("Success", "TXT exported successfully.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def pick_bin_insert(self):
        p = filedialog.askopenfilename(title="Select original BIN", filetypes=[("BIN","*.bin"),("All","*.*")])
        if p:
            self.bin_path = p
            self.lbl_bin_insert.config(text=Path(p).name, foreground='black')

    def pick_txt_insert(self):
        p = filedialog.askopenfilename(title="Select edited TXT", filetypes=[("TXT","*.txt"),("All","*.*")])
        if p:
            self.txt_path = p
            self.lbl_txt_insert.config(text=Path(p).name, foreground='black')

    def run_insert(self):
        if not self.bin_path or not self.txt_path:
            messagebox.showerror("Error", "Select both BIN and TXT first.")
            return
        dst = filedialog.asksaveasfilename(defaultextension=".bin", title="Save new BIN", filetypes=[("BIN","*.bin"),("All","*.*")])
        if dst:
            try:
                insert_from_txt(self.bin_path, self.txt_path, dst)
                messagebox.showinfo("Success", "New BIN created successfully.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

# -------------------- Main Combined App --------------------
class CombinedApp(tk.Tk):
    def __init__(self):
        super().__init__()
        

        # ----------
        self.title("Blade PSX Combined Tools - Made by Rabatini Aka Luke")
        self.geometry("600x450")        
        self.resizable(False, False)
        ttk.Style(self).theme_use('clam')
        nb = ttk.Notebook(self); nb.pack(expand=True, fill='both')
        nb.add(RLEFrame(nb), text="RLE Tool")
        nb.add(SNDVFrame(nb), text="SNDVRAM Tool")
        nb.add(ImgFrame(nb), text="Image Tool")
        nb.add(CommonFrame(nb), text="Common.dat Tool")
        nb.add(LevelFrame(nb), text="LevelBin Tool")
        self.status_var = tk.StringVar(value="Ready")
        status = ttk.Label(self, textvariable=self.status_var, relief='sunken', anchor='w')
        status.pack(side='bottom', fill='x')
          # ---------- Ícone personalizado ----------
        #self.iconbitmap(r'C:\Users\Benedicta\Downloads\output-onlinepngtools-com.ico')

if __name__ == "__main__":
    CombinedApp().mainloop()
   
