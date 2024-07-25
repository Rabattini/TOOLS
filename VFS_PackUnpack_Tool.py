import os
import struct
import zlib
import tkinter as tk
from tkinter import filedialog, messagebox

def remove_zlib_header_and_footer(data):
    """
    Remove a 7-byte header and a 4-byte footer from compressed data.
    Assumes the header is at the start and footer at the end of the data.
    """
    if len(data) > 7:
        data = data[7:]
    if len(data) > 4:
        data = data[:-4]
    return data

def unpack_vfs(input_file, output_dir):
    with open(input_file, 'rb') as f:
        magic = f.read(4)
        if magic != b'FUFS':
            raise ValueError("Invalid file format")

        unk, files_count = struct.unpack('<II', f.read(8))
        file_info = []

        for i in range(files_count):
            offset, name_crc, size = struct.unpack('<III', f.read(12))
            file_info.append((offset, name_crc, size))

        for offset, name_crc, size in file_info:
            f.seek(offset)
            file_data = f.read(size)

            file_ext_bytes = file_data[:4]
            if file_ext_bytes[0] == 0x78:
                file_ext = "zlib"
            else:
                file_ext = file_ext_bytes.decode('utf-8', errors='ignore').strip()
                file_ext = ''.join(c for c in file_ext if c.isalnum())

            output_path = os.path.join(output_dir, f"{name_crc:08x}.{file_ext}")
            with open(output_path, 'wb') as output_file:
                output_file.write(file_data)

def pack_vfs(input_dir, output_file, compression_level=6):
    compressed_files_path = os.path.join(input_dir, 'compressed_files.txt')
    compressed_files = set()

    if os.path.exists(compressed_files_path):
        with open(compressed_files_path, 'r') as f:
            compressed_files = set(f.read().splitlines())

    file_paths = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f != 'compressed_files.txt']
    file_paths.sort()

    with open(output_file, 'wb') as f:
        f.write(b'FUFS')
        f.write(struct.pack('<I', 0))
        files_count = len(file_paths)
        f.write(struct.pack('<I', files_count))

        offsets = []
        data_to_write = []
        current_offset = 12 + (files_count * 12)

        for file_path in file_paths:
            with open(file_path, 'rb') as input_file:
                file_data = input_file.read()
                file_name = os.path.basename(file_path)
                if file_name in compressed_files:
                    compressed_file_data = zlib.compress(file_data, level=compression_level)
                else:
                    compressed_file_data = file_data
                
                size = len(compressed_file_data)
                data_to_write.append(compressed_file_data)
                offsets.append((current_offset, size))
                current_offset += size

        for file_path, (offset, size) in zip(file_paths, offsets):
            name_crc = int(os.path.splitext(os.path.basename(file_path))[0], 16)
            f.write(struct.pack('<III', offset, name_crc, size))

        for data in data_to_write:
            f.write(data)
        
        final_file_size = f.tell()
        final_file_size_adjusted = final_file_size + 0x80000000
        f.seek(4)
        f.write(struct.pack('<I', final_file_size_adjusted))

def select_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        file_entry.delete(0, tk.END)
        file_entry.insert(0, file_path)

def select_directory():
    directory = filedialog.askdirectory()
    if directory:
        dir_entry.delete(0, tk.END)
        dir_entry.insert(0, directory)

def select_output_file():
    file_path = filedialog.asksaveasfilename(defaultextension=".vfs", filetypes=[("VFS files", "*.vfs"), ("All files", "*.*")])
    if file_path:
        file_entry.delete(0, tk.END)
        file_entry.insert(0, file_path)

def perform_unpack():
    input_file = file_entry.get()
    output_dir = dir_entry.get()
    if not input_file or not output_dir:
        messagebox.showerror("Error", "Please select both a file and an output directory.")
        return
    try:
        unpack_vfs(input_file, output_dir)
        messagebox.showinfo("Success", "Unpacking completed successfully.")
        clear_entries()
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

def perform_pack():
    input_dir = dir_entry.get()
    output_file = file_entry.get()
    if not input_dir or not output_file:
        messagebox.showerror("Error", "Please select both an input directory and an output file.")
        return
    try:
        pack_vfs(input_dir, output_file, compression_level=6)
        messagebox.showinfo("Success", "Packing completed successfully.")
        clear_entries()
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

def clear_entries():
    file_entry.delete(0, tk.END)
    dir_entry.delete(0, tk.END)

app = tk.Tk()
app.title("VFS Pack/Unpack Tool - Rabattini (Luke)")

frame = tk.Frame(app)
frame.pack(padx=10, pady=10)

mode_frame = tk.Frame(frame)
mode_frame.grid(row=0, column=0, columnspan=3, pady=5)

# Set unpack as the default mode
unpack_radio = tk.Radiobutton(mode_frame, text="Unpack", value="unpack", command=lambda: update_ui("unpack"))
unpack_radio.grid(row=0, column=0, padx=5)
pack_radio = tk.Radiobutton(mode_frame, text="Pack", value="pack", command=lambda: update_ui("pack"))
pack_radio.grid(row=0, column=1, padx=5)

file_label = tk.Label(frame, text="VFS File:")
file_label.grid(row=1, column=0, sticky="e")
file_entry = tk.Entry(frame, width=40)
file_entry.grid(row=1, column=1, padx=5, pady=5)
file_button = tk.Button(frame, text="Browse", command=select_file)
file_button.grid(row=1, column=2, padx=10)

dir_label = tk.Label(frame, text="Output Directory:")
dir_label.grid(row=2, column=0, sticky="e")
dir_entry = tk.Entry(frame, width=40)
dir_entry.grid(row=2, column=1, padx=5, pady=5)
dir_button = tk.Button(frame, text="Browse", command=select_directory)
dir_button.grid(row=2, column=2, padx=10)

action_button = tk.Button(frame, text="Unpack", command=perform_unpack)
action_button.grid(row=3, column=0, columnspan=3, pady=10)

def update_ui(mode):
    if mode == "unpack":
        file_label.config(text="VFS File:")
        dir_label.config(text="Output Directory:")
        file_button.config(command=select_file)
        dir_button.config(command=select_directory)
        action_button.config(text="Unpack", command=perform_unpack)
        unpack_radio.select()
    elif mode == "pack":
        file_label.config(text="Output VFS File:")
        dir_label.config(text="Input Directory:")
        file_button.config(command=select_output_file)
        dir_button.config(command=select_directory)
        action_button.config(text="Pack", command=perform_pack)
        pack_radio.select()

# Initialize UI for unpack mode by default
update_ui("unpack")

app.mainloop()
