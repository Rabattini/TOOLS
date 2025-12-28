import tkinter as tk
from tkinter import filedialog, messagebox
import struct
import os

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def load_act_palette(path: str):
    with open(path, "rb") as f:
        data = f.read()

    if len(data) < 768:
        raise ValueError("ACT inválido: arquivo menor que 768 bytes.")

    pal = []
    for i in range(256):
        r = data[i * 3 + 0]
        g = data[i * 3 + 1]
        b = data[i * 3 + 2]
        pal.append((r, g, b))

    transparent_index = None
    if len(data) >= 772:
        tail = data[-4:]
        ti = int.from_bytes(tail[2:4], "big", signed=False)
        if ti != 0xFFFF and 0 <= ti <= 255:
            transparent_index = ti

    return pal, transparent_index


class BobExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("BOB Extractor - Made by Rabatini (Luke)")
        self.root.geometry("1320x880")

        self.filepath = ""
        self.file_data = b""
        self.sprite_offsets = []

        # Paleta
        self.palette = None
        self.palette_path = ""
        self.palette_ti = None
        self.var_use_palette = tk.BooleanVar(value=True)
        self.var_transp_override = tk.StringVar(value="")

        # Preview
        self.var_zoom = tk.IntVar(value=6)
        self.var_show_aligned = tk.BooleanVar(value=False)  # default DESMARCADO
        self.var_preview_cropped = tk.BooleanVar(value=True)  # <<< RAW vs CROPPED quando não alinhado
        self.var_crop_export = tk.BooleanVar(value=True)

        # GIF (opcional)
        self.var_export_gif = tk.BooleanVar(value=False)
        self.var_gif_name = tk.StringVar(value="animation.gif")
        self.var_gif_fps = tk.IntVar(value=12)

        self._tk_img = None

        # bounds do canvas alinhado
        self.min_hdrx = 0
        self.min_hdry = 0
        self.global_w = 1
        self.global_h = 1

        self.setup_ui()

        # auto-carrega BGRPAL.act se existir na pasta
        if os.path.exists("BGRPAL.act"):
            try:
                pal, ti = load_act_palette("BGRPAL.act")
                self.palette = pal
                self.palette_ti = ti
                self.palette_path = "BGRPAL.act"
                base = os.path.basename(self.palette_path)
                extra = f" (TI={ti})" if ti is not None else " (sem TI -> usa 0)"
                self.lbl_pal.config(text=base + extra, fg="green")
            except:
                pass

    # ---------------- UI (com Scroll) ----------------
    def setup_ui(self):
        # Container da esquerda
        left_container = tk.Frame(self.root, bg="#f0f0f0")
        left_container.pack(side=tk.LEFT, fill=tk.Y)

        # Canvas rolável + scrollbar
        self.panel_canvas = tk.Canvas(left_container, width=520, bg="#f0f0f0", highlightthickness=0)
        self.panel_canvas.pack(side=tk.LEFT, fill=tk.Y, expand=False)

        scrollbar = tk.Scrollbar(left_container, orient="vertical", command=self.panel_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.panel_canvas.configure(yscrollcommand=scrollbar.set)

        # Frame interno rolável
        self.panel = tk.Frame(self.panel_canvas, padx=10, pady=10, width=500, bg="#f0f0f0")
        self.panel_window = self.panel_canvas.create_window((0, 0), window=self.panel, anchor="nw")

        # Atualiza área rolável
        def _on_frame_configure(_event=None):
            self.panel_canvas.configure(scrollregion=self.panel_canvas.bbox("all"))

        self.panel.bind("<Configure>", _on_frame_configure)

        # Ajusta largura do frame interno ao canvas
        def _on_canvas_configure(event):
            self.panel_canvas.itemconfig(self.panel_window, width=event.width)

        self.panel_canvas.bind("<Configure>", _on_canvas_configure)

        # Mousewheel no painel
        def _on_mousewheel(event):
            if event.delta:
                self.panel_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            else:
                if event.num == 4:
                    self.panel_canvas.yview_scroll(-3, "units")
                elif event.num == 5:
                    self.panel_canvas.yview_scroll(3, "units")

        self.panel_canvas.bind("<Enter>", lambda e: self.root.bind_all("<MouseWheel>", _on_mousewheel))
        self.panel_canvas.bind("<Leave>", lambda e: self.root.unbind_all("<MouseWheel>"))
        self.panel_canvas.bind("<Button-4>", _on_mousewheel)
        self.panel_canvas.bind("<Button-5>", _on_mousewheel)

        # ---------------- widgets ----------------
        p = self.panel

        tk.Label(p, text="1) Arquivo", bg="#f0f0f0", font=("Arial", 10, "bold")).pack(anchor="w")
        tk.Button(p, text="Abrir .BOB", command=self.load_file, bg="#ddd").pack(fill=tk.X, pady=5)
        self.lbl_status = tk.Label(p, text="...", bg="#f0f0f0", fg="#555", justify="left")
        self.lbl_status.pack(anchor="w")

        tk.Label(
            p,
            text=(
                "Tool para extrair arquivos BOB do jogo Conquest.\n"
                
            ),
            bg="#f0f0f0", fg="#333", justify="left", wraplength=470
        ).pack(anchor="w", pady=(8, 0))

        tk.Frame(p, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, pady=10)

        # Paleta
        tk.Label(p, text="2) Paleta", bg="#f0f0f0", font=("Arial", 10, "bold")).pack(anchor="w")
        rowp = tk.Frame(p, bg="#f0f0f0")
        rowp.pack(fill=tk.X, pady=4)
        tk.Button(rowp, text="Carregar .ACT", command=self.pick_palette, bg="#ddd").pack(side=tk.LEFT)
        self.lbl_pal = tk.Label(rowp, text="(sem paleta)", bg="#f0f0f0", fg="#555")
        self.lbl_pal.pack(side=tk.LEFT, padx=8)

        tk.Checkbutton(p, text="Usar paleta no preview/export",
                       variable=self.var_use_palette, command=self.update_preview,
                       bg="#f0f0f0").pack(anchor="w", pady=(2, 0))

        rowt = tk.Frame(p, bg="#f0f0f0")
        rowt.pack(fill=tk.X, pady=(4, 0))
        tk.Label(rowt, text="Transparente:", bg="#f0f0f0").pack(side=tk.LEFT)
        tk.Entry(rowt, textvariable=self.var_transp_override, width=6).pack(side=tk.LEFT, padx=6)
        tk.Label(rowt, text="(vazio=auto; sem TI no ACT => usa 0)", bg="#f0f0f0", fg="#666").pack(side=tk.LEFT)

        tk.Frame(p, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, pady=10)

        # Preview
        tk.Label(p, text="3) Preview", bg="#f0f0f0", font=("Arial", 10, "bold")).pack(anchor="w")
        tk.Label(p, text="Sprite Index:", bg="#f0f0f0").pack(anchor="w")
        self.slider_sprite = tk.Scale(p, from_=0, to=0, orient=tk.HORIZONTAL,
                                      command=self.update_preview, bg="#f0f0f0")
        self.slider_sprite.pack(fill=tk.X)

        tk.Label(p, text="Zoom:", bg="#f0f0f0").pack(anchor="w", pady=(5, 0))
        tk.Scale(p, from_=1, to=14, orient=tk.HORIZONTAL,
                 variable=self.var_zoom, command=self.update_preview,
                 bg="#f0f0f0").pack(fill=tk.X)

        tk.Checkbutton(p, text="Preview ALINHADO (usa hdrX/hdrY como coords)",
                       variable=self.var_show_aligned, command=self.update_preview,
                       bg="#f0f0f0").pack(anchor="w", pady=(6, 0))

        tk.Checkbutton(p, text="Preview CROPPED (quando não-alinhado)",
                       variable=self.var_preview_cropped, command=self.update_preview,
                       bg="#f0f0f0").pack(anchor="w", pady=(2, 0))

        tk.Checkbutton(p, text="Exportar PNG_CROPPED (crop por conteúdo)",
                       variable=self.var_crop_export, bg="#f0f0f0").pack(anchor="w", pady=(2, 0))

        tk.Frame(p, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, pady=10)

        # GIF
        tk.Label(p, text="4) GIF (opcional)", bg="#f0f0f0", font=("Arial", 10, "bold")).pack(anchor="w")
        gif_help = "(precisa Pillow)" if HAS_PIL else "(Pillow não instalado: GIF desabilitado)"
        tk.Checkbutton(p, text=f"Gerar GIF animado (usa PNG_ALIGNED) {gif_help}",
                       variable=self.var_export_gif, bg="#f0f0f0",
                       state=("normal" if HAS_PIL else "disabled")).pack(anchor="w", pady=(4, 0))

        rowg = tk.Frame(p, bg="#f0f0f0")
        rowg.pack(fill=tk.X, pady=(4, 0))
        tk.Label(rowg, text="Nome:", bg="#f0f0f0").pack(side=tk.LEFT)
        tk.Entry(rowg, textvariable=self.var_gif_name).pack(side=tk.LEFT, padx=6, fill=tk.X, expand=True)

        rowf = tk.Frame(p, bg="#f0f0f0")
        rowf.pack(fill=tk.X, pady=(4, 0))
        tk.Label(rowf, text="FPS:", bg="#f0f0f0").pack(side=tk.LEFT)
        tk.Entry(rowf, textvariable=self.var_gif_fps, width=6).pack(side=tk.LEFT, padx=6)
        tk.Label(rowf, text="(ex: 8, 12, 15)", bg="#f0f0f0", fg="#666").pack(side=tk.LEFT)

        self.lbl_info = tk.Label(p, text="Info: -", bg="#f0f0f0", fg="#222", justify="left")
        self.lbl_info.pack(anchor="w", pady=(10, 0))

        tk.Frame(p, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, pady=10)

        tk.Button(p, text="EXTRAIR TUDO (BIN + PNG + META)",
                  command=self.export_all, bg="#4CAF50", fg="white",
                  font=("Arial", 10, "bold"), height=2).pack(fill=tk.X, pady=8)

        # Canvas de preview (direita)
        canvas_area = tk.Frame(self.root, bg="#202020")
        canvas_area.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        self.canvas = tk.Canvas(canvas_area, bg="#202020", highlightthickness=0)
        self.canvas.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

    # ---------------- Paleta ----------------
    def get_transparent_index(self):
        txt = self.var_transp_override.get().strip()
        if txt:
            try:
                v = int(txt)
                if 0 <= v <= 255:
                    return v
            except:
                pass
        if self.palette is not None and self.palette_ti is None:
            return 0
        return self.palette_ti

    def idx_to_rgba(self, idx_val: int):
        if self.var_use_palette.get() and self.palette:
            r, g, b = self.palette[idx_val]
            ti = self.get_transparent_index()
            if ti is not None and idx_val == ti:
                return (r, g, b, 0)
            return (r, g, b, 255)
        v = idx_val
        return (v, v, v, 255)

    def pick_palette(self):
        path = filedialog.askopenfilename(filetypes=[("ACT Palette", "*.act"), ("All Files", "*.*")])
        if not path:
            return
        try:
            pal, ti = load_act_palette(path)
            self.palette = pal
            self.palette_ti = ti
            self.palette_path = path
            base = os.path.basename(path)
            extra = f" (TI={ti})" if ti is not None else " (sem TI -> usa 0)"
            self.lbl_pal.config(text=base + extra, fg="green")
            self.update_preview()
        except Exception as e:
            messagebox.showerror("Erro paleta", str(e))

    # ---------------- GIF helper (FIX Pillow novo) ----------------
    def rgba_to_gif_frame(self, rgba_img: "Image.Image"):
        """
        Tive problema com o pyllow instalado, atualizer ele e alguas coisas mudaram como:
        Pillow recente: RGBA só quantiza com FASTOCTREE (2) ou libimagequant (3).
        Usei FASTOCTREE e apliquei transparência via alpha.
        """
        if rgba_img.mode != "RGBA":
            rgba_img = rgba_img.convert("RGBA")

        alpha = rgba_img.getchannel("A")

        # quantiza RGB (sem alpha)
        rgb = rgba_img.convert("RGB")
        p = rgb.quantize(colors=255, method=Image.FASTOCTREE)
        p = p.copy()

        transparent_index = 255

        palette = p.getpalette() or []
        if len(palette) < 768:
            palette += [0] * (768 - len(palette))
        p.putpalette(palette[:768])

        px = p.load()
        a = alpha.load()
        w, h = p.size
        for y in range(h):
            for x in range(w):
                if a[x, y] == 0:
                    px[x, y] = transparent_index

        p.info["transparency"] = transparent_index
        p.info["disposal"] = 2
        return p

    # ---------------- BOB parsing ----------------
    def load_file(self):
        filename = filedialog.askopenfilename(filetypes=[("BOB Files", "*.BOB"), ("All Files", "*.*")])
        if not filename:
            return

        self.filepath = filename
        try:
            with open(filename, "rb") as f:
                self.file_data = f.read()

            if self.file_data[:4] != b'PBOB':
                messagebox.showwarning("Aviso", "Header não é PBOB (vou tentar ler mesmo).")

            first_offset_val = struct.unpack('<I', self.file_data[4:8])[0]
            count = first_offset_val // 4

            self.sprite_offsets = []
            for i in range(count):
                pos = 4 + (i * 4)
                val = struct.unpack('<I', self.file_data[pos:pos+4])[0]
                self.sprite_offsets.append(4 + val)

            self.slider_sprite.config(to=max(0, len(self.sprite_offsets) - 1))
            self.lbl_status.config(text=f"{count} sprites carregados.", fg="green")

            self.compute_global_bounds()
            self.update_preview()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def get_sprite_blob(self, idx):
        start = self.sprite_offsets[idx]
        end = self.sprite_offsets[idx + 1] if idx < len(self.sprite_offsets) - 1 else len(self.file_data)
        return self.file_data[start:end]

    def parse_header(self, blob):
        if len(blob) < 8:
            return None
        hdrx, hdry, w, h = struct.unpack('<hhHH', blob[:8])  # hdr signed
        if w <= 0 or h <= 0:
            return None
        if len(blob) < 8 + h * 2:
            return None
        row_off = struct.unpack('<' + ('H' * h), blob[8:8 + h * 2])
        return hdrx, hdry, w, h, row_off

    def compute_global_bounds(self):
        minsx = None
        minsy = None
        maxx2 = None
        maxy2 = None

        for i in range(len(self.sprite_offsets)):
            blob = self.get_sprite_blob(i)
            parsed = self.parse_header(blob)
            if not parsed:
                continue
            hdrx, hdry, w, h, _ = parsed

            minsx = hdrx if minsx is None else min(minsx, hdrx)
            minsy = hdry if minsy is None else min(minsy, hdry)
            maxx2 = (hdrx + w) if maxx2 is None else max(maxx2, hdrx + w)
            maxy2 = (hdry + h) if maxy2 is None else max(maxy2, hdry + h)

        if minsx is None:
            self.min_hdrx, self.min_hdry = 0, 0
            self.global_w, self.global_h = 1, 1
        else:
            self.min_hdrx, self.min_hdry = minsx, minsy
            self.global_w = max(1, maxx2 - minsx)
            self.global_h = max(1, maxy2 - minsy)

    # ---------------- RLE CORRIGIDO ----------------
    def decode_sprite(self, idx):
        blob = self.get_sprite_blob(idx)
        parsed = self.parse_header(blob)
        if not parsed:
            return [], 0, 0, 0, 0, "SEM_HEADER"

        hdrx, hdry, w, h, row_off = parsed

        stream_start = 8 + row_off[0]
        if stream_start < 8 or stream_start >= len(blob):
            stream_start = 8 + h * 2

        stream = blob[stream_start:]

        pixels = []
        x = 0
        y = 0
        i = 0

        while i < len(stream) and y < h:
            b = stream[i]
            i += 1

            if b == 0x80:
                x = 0
                y += 1
                continue

            if b >= 0x81:
                x += (256 - b)
                continue

            count = b
            if count == 0:
                continue

            for _ in range(count):
                if i >= len(stream) or y >= h:
                    break
                pv = stream[i]
                i += 1
                if 0 <= x < w and 0 <= y < h:
                    pixels.append((x, y, pv))
                x += 1

        return pixels, hdrx, hdry, w, h, f"RLE_OK stream={stream_start}"

    # ---------------- Crop / Preview ----------------
    def crop_pixels(self, pixels, w, h):
        if not pixels:
            return pixels, w, h, 0, 0, (0, 0, -1, -1)
        minx = min(px for px, py, c in pixels)
        miny = min(py for px, py, c in pixels)
        maxx = max(px for px, py, c in pixels)
        maxy = max(py for px, py, c in pixels)
        new_w = (maxx - minx) + 1
        new_h = (maxy - miny) + 1
        shifted = [(px - minx, py - miny, c) for px, py, c in pixels]
        return shifted, new_w, new_h, minx, miny, (minx, miny, maxx, maxy)

    def update_preview(self, _=None):
        if not self.sprite_offsets:
            return

        idx = int(self.slider_sprite.get())
        pixels, hdrx, hdry, w, h, mode = self.decode_sprite(idx)

        show_aligned = self.var_show_aligned.get()
        zoom = int(self.var_zoom.get())

        self.canvas.delete("all")

        if show_aligned:
            pw, ph = self.global_w, self.global_h
            place_x = hdrx - self.min_hdrx
            place_y = hdry - self.min_hdry
            draw_pixels = pixels
            bbox_txt = "global"
        else:
            if self.var_preview_cropped.get():
                draw_pixels, pw, ph, _, _, bbox = self.crop_pixels(pixels, w, h)
                bbox_txt = str(bbox)
            else:
                draw_pixels = pixels
                pw, ph = w, h
                bbox_txt = "raw"
            place_x = 0
            place_y = 0

        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        ox = max((cw - pw * zoom) // 2, 0)
        oy = max((ch - ph * zoom) // 2, 0)

        self.lbl_info.config(
            text=(
                f"Sprite {idx}\n"
                f"hdrX={hdrx} hdrY={hdry}  W={w} H={h}\n"
                f"Preview={'ALINHADO' if show_aligned else ('CROPPED' if self.var_preview_cropped.get() else 'RAW')}  zoom={zoom}\n"
                f"{mode} | bbox={bbox_txt}\n"
                f"Palette={'ON' if (self.palette and self.var_use_palette.get()) else 'OFF'} "
                f"TI={self.get_transparent_index()}  ({os.path.basename(self.palette_path) if self.palette_path else '-'})"
            )
        )

        if HAS_PIL:
            img = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
            for x, y, c in draw_pixels:
                X = place_x + x
                Y = place_y + y
                if 0 <= X < pw and 0 <= Y < ph:
                    img.putpixel((X, Y), self.idx_to_rgba(c))

            img_zoom = img.resize((pw * zoom, ph * zoom), resample=Image.NEAREST)
            self._tk_img = ImageTk.PhotoImage(img_zoom)
            self.canvas.create_image(ox, oy, image=self._tk_img, anchor="nw")

        self.canvas.create_rectangle(ox, oy, ox + pw * zoom, oy + ph * zoom, outline="red", dash=(2, 2))

    # ---------------- Export ----------------
    def export_all(self):
        if not self.sprite_offsets:
            return

        out_dir = filedialog.askdirectory()
        if not out_dir:
            return

        bin_dir = os.path.join(out_dir, "BIN")
        png_dir = os.path.join(out_dir, "PNG")
        png_crop_dir = os.path.join(out_dir, "PNG_CROPPED")
        png_align_dir = os.path.join(out_dir, "PNG_ALIGNED")
        meta_dir = os.path.join(out_dir, "META")

        os.makedirs(bin_dir, exist_ok=True)
        os.makedirs(png_dir, exist_ok=True)
        os.makedirs(png_crop_dir, exist_ok=True)
        os.makedirs(png_align_dir, exist_ok=True)
        os.makedirs(meta_dir, exist_ok=True)

        do_crop = self.var_crop_export.get()
        gif_frames = []

        for i in range(len(self.sprite_offsets)):
            pixels, hdrx, hdry, w, h, mode = self.decode_sprite(i)
            if w <= 0 or h <= 0:
                continue

            # BIN
            buf = bytearray(w * h)
            for x, y, c in pixels:
                if 0 <= x < w and 0 <= y < h:
                    buf[y * w + x] = c
            with open(os.path.join(bin_dir, f"sprite_{i:03d}.bin"), "wb") as f:
                f.write(buf)

            if HAS_PIL:
                # PNG normal
                img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                for x, y, c in pixels:
                    img.putpixel((x, y), self.idx_to_rgba(c))
                img.save(os.path.join(png_dir, f"sprite_{i:03d}.png"))

                # PNG cropped
                if do_crop:
                    pc, cw, ch, _, _, _ = self.crop_pixels(pixels, w, h)
                    imgc = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
                    for x, y, c in pc:
                        imgc.putpixel((x, y), self.idx_to_rgba(c))
                    imgc.save(os.path.join(png_crop_dir, f"sprite_{i:03d}.png"))

                # PNG aligned
                pw, ph = self.global_w, self.global_h
                ax = hdrx - self.min_hdrx
                ay = hdry - self.min_hdry
                imga = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
                for x, y, c in pixels:
                    X = ax + x
                    Y = ay + y
                    if 0 <= X < pw and 0 <= Y < ph:
                        imga.putpixel((X, Y), self.idx_to_rgba(c))
                imga.save(os.path.join(png_align_dir, f"sprite_{i:03d}.png"))

                if self.var_export_gif.get():
                    gif_frames.append(imga.copy())

            # META
            with open(os.path.join(meta_dir, f"sprite_{i:03d}.txt"), "w", encoding="utf-8") as f:
                f.write(f"sprite={i}\n")
                f.write(f"hdrx={hdrx}\n")
                f.write(f"hdry={hdry}\n")
                f.write(f"w={w}\n")
                f.write(f"h={h}\n")
                f.write(f"decoder={mode}\n")
                f.write(f"skip=255-b\n")
                f.write(f"global_min_hdr=({self.min_hdrx},{self.min_hdry})\n")
                f.write(f"global_size=({self.global_w},{self.global_h})\n")
                f.write(f"palette={self.palette_path}\n")
                f.write(f"transparent={self.get_transparent_index()}\n")

        # GIF
        if self.var_export_gif.get() and HAS_PIL and gif_frames:
            try:
                fps = max(1, int(self.var_gif_fps.get()))
            except:
                fps = 12
            duration_ms = int(1000 / fps)

            name = (self.var_gif_name.get().strip() or "animation.gif")
            if not name.lower().endswith(".gif"):
                name += ".gif"
            gif_path = os.path.join(out_dir, name)

            frames_p = [self.rgba_to_gif_frame(fr) for fr in gif_frames]
            frames_p[0].save(
                gif_path,
                save_all=True,
                append_images=frames_p[1:],
                duration=duration_ms,
                loop=0,
                disposal=2,
                optimize=False
            )

        messagebox.showinfo("Fim", "Exportação concluída! (BIN + PNG + META + GIF opcional)")


if __name__ == "__main__":
    root = tk.Tk()
    app = BobExtractor(root)
    root.mainloop()
