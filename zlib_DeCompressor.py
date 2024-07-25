import os
import zlib
import tkinter as tk
from tkinter import filedialog, messagebox

HEADER_SIZE = 12  # Tamanho do cabeçalho

def save_header(data, file_path):
    header = data[:HEADER_SIZE]
    with open(file_path, 'wb') as f:
        f.write(header)

def read_header(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            return f.read(HEADER_SIZE)
    return b''

def get_file_extension(data):
    # Obtemos os primeiros 4 bytes como extensão
    if len(data) >= 4:
        extension = data[:4].decode('utf-8', errors='ignore').strip()
        return extension if extension else 'bin'
    return 'bin'

def get_file_extension_from_hdr(header_file):
    if header_file and os.path.exists(header_file):
        with open(header_file, 'rb') as f:
            header = f.read(4)
            return header.decode('utf-8', errors='ignore').strip() if len(header) == 4 else 'zlib'
    return 'zlib'  # Padrão se não houver cabeçalho

def compress_file(input_file, compress_level, header_file):
    if compress_level < 0 or compress_level > 9:
        raise ValueError("O nível de compressão deve estar entre 0 e 9.")
    
    # Se um arquivo de cabeçalho for especificado, lê-lo
    header = read_header(header_file) if header_file and os.path.exists(header_file) else b''

    with open(input_file, 'rb') as f:
        data = f.read()
    
    # Comprime o arquivo inteiro
    compressed_data = zlib.compress(data, level=compress_level)
    
    # Concatena cabeçalho e dados comprimidos apenas se o cabeçalho estiver presente
    final_data = header + compressed_data if len(header) == HEADER_SIZE else compressed_data
    
    # Define a extensão com base no cabeçalho, se fornecido
    extension = get_file_extension_from_hdr(header_file) if header_file and os.path.exists(header_file) else 'zlib'
    
    # Define o nome do arquivo de saída com a nova extensão
    base_name = os.path.splitext(input_file)[0]
    output_file = f"{base_name}.{extension}"
    
    with open(output_file, 'wb') as f:
        f.write(final_data)

def decompress_file(input_file):
    base_name, _ = os.path.splitext(input_file)

    with open(input_file, 'rb') as f:
        data = f.read()

    # Se o arquivo for muito pequeno, não pode ter cabeçalho
    if len(data) < HEADER_SIZE:
        raise ValueError("Arquivo muito pequeno para ter um cabeçalho de tamanho esperado.")

    # Verifica se o primeiro byte indica compressão zlib
    if data[:1] == b'\x78':
        # Dados são zlib diretamente
        data_to_decompress = data
        decompressed_data = zlib.decompress(data_to_decompress)
        extension = get_file_extension(decompressed_data)
        output_file = f"{base_name}.{extension}"

        with open(output_file, 'wb') as f:
            f.write(decompressed_data)
    else:
        # Dados são FUFS
        if len(data) < HEADER_SIZE:
            raise ValueError("Arquivo muito pequeno para ter um cabeçalho de tamanho esperado.")
        header = data[:HEADER_SIZE]
        data_to_decompress = data[HEADER_SIZE:]
        try:
            decompressed_data = zlib.decompress(data_to_decompress)
            extension = get_file_extension(decompressed_data)
            output_file = f"{base_name}.{extension}"
            with open(output_file, 'wb') as f:
                f.write(decompressed_data)
            # Salva o cabeçalho automaticamente
            header_file = f"{base_name}.hdr"
            save_header(data, header_file)
        except zlib.error as e:
            raise ValueError(f"Erro ao descomprimir o arquivo: {e}")

def select_input_file():
    file_path = filedialog.askopenfilename(title="Selecione o arquivo", filetypes=[("Todos os arquivos", "*.*")])
    if file_path:
        input_entry.delete(0, tk.END)
        input_entry.insert(0, file_path)

def select_header_file():
    file_path = filedialog.askopenfilename(title="Selecione o arquivo de cabeçalho", filetypes=[("Arquivos HDR", "*.hdr"), ("Todos os arquivos", "*.*")])
    if file_path:
        header_entry.delete(0, tk.END)
        header_entry.insert(0, file_path)

def compress_action():
    input_file = input_entry.get()
    header_file = header_entry.get() or None
    try:
        compress_level = int(compress_level_entry.get())
        compress_file(input_file, compress_level, header_file)
        messagebox.showinfo("Sucesso", f"Arquivo comprimido com sucesso.")
    except ValueError as e:
        messagebox.showerror("Erro", str(e))
    finally:
        # Limpar campos após a operação
        input_entry.delete(0, tk.END)
        header_entry.delete(0, tk.END)
        compress_level_entry.delete(0, tk.END)

def decompress_action():
    input_file = input_entry.get()
    try:
        decompress_file(input_file)
        messagebox.showinfo("Sucesso", f"Arquivo descomprimido com sucesso.")
    except ValueError as e:
        messagebox.showerror("Erro", str(e))
    finally:
        # Limpar campos após a operação
        input_entry.delete(0, tk.END)
        header_entry.delete(0, tk.END)

def set_mode(mode):
    if mode == "compress":
        compress_button.grid(row=6, column=1, padx=10, pady=20)
        decompress_button.grid_forget()
        header_label.grid(row=3, column=0, padx=10, pady=5, sticky="e")
        header_entry.grid(row=3, column=1, padx=10, pady=5)
        header_button.grid(row=3, column=2, padx=10, pady=5)
    elif mode == "decompress":
        decompress_button.grid(row=6, column=1, padx=10, pady=20)
        compress_button.grid_forget()
        header_label.grid_forget()
        header_entry.grid_forget()
        header_button.grid_forget()

# Cria a janela principal
root = tk.Tk()
root.title("Compressor/Descompressor Zlib - Rabattini (Luke)")

# Layout da interface gráfica
tk.Label(root, text="Arquivo de entrada:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
input_entry = tk.Entry(root, width=50)
input_entry.grid(row=0, column=1, padx=10, pady=5)
tk.Button(root, text="Selecionar", command=select_input_file).grid(row=0, column=2, padx=10, pady=5)

tk.Label(root, text="Nível de compressão (0-9):").grid(row=1, column=0, padx=10, pady=5, sticky="e")
compress_level_entry = tk.Entry(root, width=10)
compress_level_entry.grid(row=1, column=1, padx=10, pady=5)

header_label = tk.Label(root, text="Arquivo de cabeçalho:")
header_entry = tk.Entry(root, width=50)
header_button = tk.Button(root, text="Selecionar Cabeçalho", command=select_header_file)

# Botões de ação
compress_button = tk.Button(root, text="Comprimir", command=compress_action)
decompress_button = tk.Button(root, text="Descomprimir", command=decompress_action)

# Selecionar o modo inicial (descompressão por padrão)
mode_var = tk.StringVar(value="decompress")
tk.Radiobutton(root, text="Compressão", variable=mode_var, value="compress", command=lambda: set_mode("compress")).grid(row=2, column=0, padx=10, pady=10)
tk.Radiobutton(root, text="Descompressão", variable=mode_var, value="decompress", command=lambda: set_mode("decompress")).grid(row=2, column=1, padx=10, pady=10)

# Exibir o botão de descompressão por padrão
decompress_button.grid(row=6, column=1, padx=10, pady=20)

# Inicia o loop da interface gráfica
root.mainloop()
