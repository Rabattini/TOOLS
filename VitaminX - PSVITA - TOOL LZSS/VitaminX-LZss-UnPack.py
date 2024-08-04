import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import struct
import os
import re
import lzss
import time

def show_processing_window():
    global processing_window
    processing_window = tk.Toplevel(root)
    processing_window.title("Processing")
    tk.Label(processing_window, text="Processing...", padx=20, pady=20).pack()
    processing_window.grab_set()  # Make the processing window modal

def close_processing_window():
    global processing_window
    processing_window.destroy()

def read_lzss_file(filename):
    with open(filename, 'rb') as file:
        idstring = file.read(4).decode('ascii')
        if idstring != "HLZS":
            raise ValueError("File is not a valid LZSS file")

        file.seek(0x04)
        fixo = struct.unpack('<I', file.read(4))[0]

        file.seek(0x08)
        zsize = struct.unpack('<I', file.read(4))[0]

        file.seek(0x0C)
        size = struct.unpack('<I', file.read(4))[0]

        file.seek(0x20)
        compressed_data = file.read(zsize)

    decompressed_data = lzss.decompress(compressed_data, size)
    return decompressed_data, fixo

def compress_file():
    source_path = source_path_entry.get()
    dest_path = dest_path_entry.get()
    process_multiple = multiple_files_var.get()

    if not source_path:
        messagebox.showwarning("Attention", "Please select a folder to compress." if process_multiple else "Please select a file to compress.")
        return

    if not dest_path:
        messagebox.showwarning("Attention", "Please select the location to save the compressed file.")
        return

    show_processing_window()
    root.update()  # Update the GUI to show the processing window

    try:
        if process_multiple:
            # Process multiple files
            for filename in os.listdir(source_path):
                if filename.endswith('.dec'):
                    file_path = os.path.join(source_path, filename)
                    with open(file_path, 'rb') as file:
                        data = file.read()

                    compressed_data = lzss.compress(data)
                    fixo = 4096

                    idstring = "HLZS"
                    zsize = len(compressed_data)
                    size = len(data)
                    header = struct.pack('<4sIII16s', idstring.encode('ascii'), fixo, zsize, size, b'\x00'*16)

                    output_path = os.path.join(dest_path, filename + '.lzss')

                    with open(output_path, 'wb') as file:
                        file.write(header)
                        file.write(compressed_data)

            messagebox.showinfo("Success", f"Compression completed successfully!\nFiles saved to: {dest_path}")

        else:
            # Process a single file
            with open(source_path, 'rb') as file:
                data = file.read()

            compressed_data = lzss.compress(data)
            fixo = 4096

            idstring = "HLZS"
            zsize = len(compressed_data)
            size = len(data)
            header = struct.pack('<4sIII16s', idstring.encode('ascii'), fixo, zsize, size, b'\x00'*16)

            output_path = os.path.join(dest_path, os.path.basename(source_path) + '.lzss')

            with open(output_path, 'wb') as file:
                file.write(header)
                file.write(compressed_data)

            messagebox.showinfo("Success", f"Compression completed successfully!\nFile saved as: {output_path}")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

    close_processing_window()

def decompress_file():
    source_path = source_path_entry.get()
    dest_path = dest_path_entry.get()
    process_multiple = multiple_files_var.get()

    if not source_path:
        messagebox.showwarning("Attention", "Please select a folder to decompress." if process_multiple else "Please select a file to decompress.")
        return

    if not dest_path:
        messagebox.showwarning("Attention", "Please select the location to save the decompressed file.")
        return

    show_processing_window()
    root.update()  # Update the GUI to show the processing window

    try:
        if process_multiple:
            # Process multiple files
            for filename in os.listdir(source_path):
                if filename.endswith('.lzss'):
                    file_path = os.path.join(source_path, filename)
                    decompressed_data, _ = read_lzss_file(file_path)

                    output_path = os.path.join(dest_path, filename + '.dec')

                    with open(output_path, 'wb') as file:
                        file.write(decompressed_data)

            messagebox.showinfo("Success", f"Decompression completed successfully!\nFiles saved to: {dest_path}")

        else:
            # Process a single file
            decompressed_data, _ = read_lzss_file(source_path)

            output_path = os.path.join(dest_path, os.path.basename(source_path) + '.dec')

            with open(output_path, 'wb') as file:
                file.write(decompressed_data)

            messagebox.showinfo("Success", f"Decompression completed successfully!\nFile saved as: {output_path}")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

    close_processing_window()

def unpack_hlzs_file():
    source_path = source_path_entry.get()
    dest_path = dest_path_entry.get()
    process_multiple = multiple_files_var.get()

    if not source_path:
        messagebox.showwarning("Attention", "Please select a file to unpack.")
        return

    if not dest_path:
        messagebox.showwarning("Attention", "Please select the destination directory.")
        return

    show_processing_window()
    root.update()  # Update the GUI to show the processing window

    try:
        if process_multiple:
            # Process multiple files
            for filename in os.listdir(source_path):
                if filename.endswith('.hlzs'):
                    file_path = os.path.join(source_path, filename)
                    unpack_hlzs(file_path, dest_path)

            messagebox.showinfo("Success", f"Files unpacked and saved to: {dest_path}")

        else:
            # Process a single file
            unpack_hlzs(source_path, dest_path)
            messagebox.showinfo("Success", f"Files unpacked and saved to: {dest_path}")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

    close_processing_window()

def unpack_hlzs(file_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(file_path, 'rb') as f:
        data = f.read()

    offset = 0
    file_index = 1
    while offset < len(data):
        header_index = data.find(b'HLZS', offset)
        if header_index == -1:
            break

        next_header_index = data.find(b'HLZS', header_index + 4)
        if next_header_index == -1:
            next_header_index = len(data)

        compressed_data = data[header_index:next_header_index]
        
        output_file_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(file_path))[0]}_{file_index}.lzss")
        with open(output_file_path, 'wb') as out_file:
            out_file.write(compressed_data)
        
        offset = next_header_index
        file_index += 1

def numerical_sort(value):
    numbers = re.findall(r'\d+', value)
    return list(map(int, numbers))

def pack_hlzs():
    input_dir = source_path_entry.get()
    dest_path = dest_path_entry.get()

    if not input_dir:
        messagebox.showwarning("Attention", "Please select a folder to pack.")
        return

    if not dest_path:
        messagebox.showwarning("Attention", "Please select the location to save the compressed file.")
        return

    show_processing_window()
    root.update()  # Update the GUI to show the processing window

    try:
        output_file_path = os.path.join(dest_path, 'output.bin')
        with open(output_file_path, 'wb') as out_file:
            files = [f for f in os.listdir(input_dir) if f.endswith('.lzss')]
            files.sort(key=numerical_sort)

            for filename in files:
                lzss_file_path = os.path.join(input_dir, filename)
                with open(lzss_file_path, 'rb') as lzss_file:
                    compressed_data = lzss_file.read()
                out_file.write(compressed_data)

        messagebox.showinfo("Success", f"Compressed file created: {output_file_path}")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

    close_processing_window()

def browse_source_file():
    if multiple_files_var.get():
        directory_path = filedialog.askdirectory(title="Select the source folder")
        source_path_entry.delete(0, tk.END)
        source_path_entry.insert(0, directory_path)
    else:
        file_path = filedialog.askopenfilename(title="Select the source file")
        if file_path:
            source_path_entry.delete(0, tk.END)
            source_path_entry.insert(0, file_path)

def browse_dest_directory():
    directory_path = filedialog.askdirectory(title="Select the destination folder")
    dest_path_entry.delete(0, tk.END)
    dest_path_entry.insert(0, directory_path)

# Main window setup
root = tk.Tk()
root.title("LZSS Tool VitaminX - PsV - Rabattini aka Luke")

# Source file/folder entry field
tk.Label(root, text="Source File/Folder:").grid(row=0, column=0, padx=10, pady=10)
source_path_entry = tk.Entry(root, width=50)
source_path_entry.grid(row=1, column=0, padx=10, pady=10)

# Browse button for source
tk.Button(root, text="Browse Source File", command=browse_source_file).grid(row=1, column=1, padx=10, pady=10)

# Destination directory entry field
tk.Label(root, text="Destination Folder:").grid(row=2, column=0, padx=10, pady=10)
dest_path_entry = tk.Entry(root, width=50)
dest_path_entry.grid(row=3, column=0, padx=10, pady=10)

# Browse button for destination
tk.Button(root, text="Browse Destination Directory", command=browse_dest_directory).grid(row=3, column=1, padx=10, pady=10)

# Checkboxes for processing mode
multiple_files_var = tk.BooleanVar()
multiple_files_checkbox = tk.Checkbutton(root, text="Process multiple files", variable=multiple_files_var)
multiple_files_checkbox.grid(row=4, column=0, padx=10, pady=10)

# Action buttons
tk.Button(root, text="Decompress LZSS", command=decompress_file).grid(row=5, column=0, padx=10, pady=10)
tk.Button(root, text="Compress LZSS", command=compress_file).grid(row=5, column=1, padx=10, pady=10)
tk.Button(root, text="Unpack HPB", command=unpack_hlzs_file).grid(row=6, column=0, padx=10, pady=10)
tk.Button(root, text="Pack HPB", command=pack_hlzs).grid(row=6, column=1, padx=10, pady=10)

# Main loop execution
root.mainloop()
