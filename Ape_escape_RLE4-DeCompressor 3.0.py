import tkinter as tk
from tkinter import filedialog, messagebox
import os


def compress_rle4(data):
    compressed_data = bytearray()
    src = 0

    while src < len(data):
        run_start = src
        run_value = data[src]
        src += 1

        # Encontre o comprimento da corrida
        while src < len(data) and data[src] == run_value:
            src += 1

        run_length = src - run_start

        if run_length > 2:
            # Corridas longas
            while run_length > 255:
                compressed_data.append((run_value << 4) | run_value)
                compressed_data.append(255)
                run_length -= 255
            compressed_data.append((run_value << 4) | run_value)
            compressed_data.append(run_length - 2)
        elif run_length == 2:
            # Corridas de comprimento 2
            compressed_data.append((run_value << 4) | run_value)
            compressed_data.append(0)  # Padding para manter o alinhamento
        elif run_length == 1:
            # Byte único
            if src < len(data):
                next_value = data[src]
                src += 1
                compressed_data.append((run_value << 4) | (next_value & 0x0F))
            else:
                compressed_data.append((run_value << 4) | 0)  # Padding

    # Ajuste o próximo byte após uma sequência de 0xFF
    i = 0
    while i < len(compressed_data) - 1:
        if compressed_data[i] == 0xFF:
            count_ff = 1
            while i + count_ff < len(compressed_data) and compressed_data[i + count_ff] == 0xFF:
                count_ff += 1

            # Verifica se o próximo byte é diferente de 0xFF e ajusta-o
            next_index = i + count_ff
            if next_index < len(compressed_data) and compressed_data[next_index] != 0xFF:
                compressed_data[next_index] = (compressed_data[next_index] - (count_ff - 1)) & 0xFF

            i = next_index
        else:
            i += 1

    # Garante que o último byte esteja completo
    if len(compressed_data) % 2 != 0:
        compressed_data.append(0)

    return bytes(compressed_data)




def decompress_rle8(data, width, height):
    output = bytearray()
    src = 0
    numpixels = 0

    while numpixels < width * height:
        if src >= len(data):
            break

        color1 = data[src] >> 4
        color2 = (data[src] & 0x0f) + 1
        src += 1

        if color1 == color2:
            if src >= len(data):
                break
            length = data[src] + 2
            src += 1
            for _ in range(length):
                output.extend([color1, color1])
                numpixels += 2
                if numpixels >= width * height:
                    break
        else:
            output.extend([color1, color2])
            numpixels += 2
            if numpixels < width * height:
                output.extend([color1, color2])
                numpixels += 2

    return bytes(output[:width * height])


def decompress_rle4(data, width, height):
    output_nibbles = bytearray()
    src = 0
    numpixels = 0

    while numpixels < width * height:
        if src >= len(data):
            break

        nibble1 = data[src] >> 4
        nibble2 = data[src] & 0x0f
        src += 1

        if nibble1 == nibble2:
            if src >= len(data):
                break
            length = data[src] + 2
            src += 1
            for _ in range(length):
                output_nibbles.append(nibble2)
                numpixels += 2
                if numpixels >= width * height:
                    break
        else:
            output_nibbles.append(nibble1)
            output_nibbles.append(nibble2)
            numpixels += 2

    output_nibbles = output_nibbles[:width * height]

    output_bytes = bytearray()
    for i in range(0, len(output_nibbles) - 1, 2):
        output_bytes.append((output_nibbles[i] << 4) | output_nibbles[i + 1])

    return bytes(output_bytes)


def prepare_image_data(image_path):
    with open(image_path, 'rb') as file:
        data = file.read()
        nibbles = []
        for byte in data:
            nibbles.append(byte >> 4)
            nibbles.append(byte & 0x0F)
        return nibbles


def save_compressed_data(file_path, data):
    with open(file_path, 'wb') as file:
        file.write(data)


def decompress_tim(file_path):
    with open(file_path, 'rb') as file:
        header = file.read(0x60)
        method = header[2]

        file.seek(0x3c)
        width = int.from_bytes(file.read(2), byteorder='little') * 4
        height = int.from_bytes(file.read(2), byteorder='little') * 2

        file.seek(0x60)
        compressed_data = file.read()

        if method == 0x02:
            decompressed_data = decompress_rle4(compressed_data, width, height)
        elif method == 0x01:
            decompressed_data = decompress_rle8(compressed_data, width, height)
        else:
            raise ValueError(f"Método de compressão não suportado: {method}")

    header_file_path = file_path + ".hdr"
    with open(header_file_path, 'wb') as hdr_file:
        hdr_file.write(header)

    output_file_path = file_path + ".dec"
    with open(output_file_path, 'wb') as output_file:
        output_file.write(decompressed_data)

    return header_file_path, output_file_path


def compress_tim(file_path, header_path):
    image_data = prepare_image_data(file_path)
    compressed_data = compress_rle4(image_data)

    output_file_path = file_path + ".rle4"
    with open(output_file_path, 'wb') as output_file:
        with open(header_path, 'rb') as header_file:
            output_file.write(header_file.read())
        output_file.write(compressed_data)

    return output_file_path


def decompress_all_rle4_in_folder(folder_path):
    extracted_folder = os.path.join(folder_path, "extracted")
    os.makedirs(extracted_folder, exist_ok=True)

    for filename in os.listdir(folder_path):
        if filename.endswith(".rle4"):
            file_path = os.path.join(folder_path, filename)
            header_file_path, output_file_path = decompress_tim(file_path)

            # Move the decompressed file to the 'extracted' folder
            new_output_file_path = os.path.join(extracted_folder, os.path.basename(output_file_path))
            os.rename(output_file_path, new_output_file_path)
            os.rename(header_file_path, os.path.join(extracted_folder, os.path.basename(header_file_path)))


class CompressionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("APE ESCAPE(PSX) - RLE4 - Compressor/Decompressor")

        self.mode = tk.IntVar(value=1)  # 1 para descompressão, 2 para compressão
        self.decompress_mode = tk.IntVar(value=1)  # 1 para individual, 2 para múltiplos

        self.file_path_var = tk.StringVar()
        self.header_path_var = tk.StringVar()

        # Widgets para seleção de modo
        tk.Label(root, text="Modo:").grid(row=0, column=0, pady=5)
        self.decompress_rb = tk.Radiobutton(root, text="Descomprimir", variable=self.mode, value=1, command=self.update_ui)
        self.compress_rb = tk.Radiobutton(root, text="Comprimir", variable=self.mode, value=2, command=self.update_ui)
        self.decompress_rb.grid(row=0, column=1, padx=5)
        self.compress_rb.grid(row=0, column=2, padx=5)

        # Widgets para seleção de arquivo
        self.file_label = tk.Label(root, text="Arquivo/Pasta:")
        self.file_entry = tk.Entry(root, textvariable=self.file_path_var, width=50)
        self.browse_file_button = tk.Button(root, text="Browse", command=self.browse_file)

        # Widgets para arquivo de cabeçalho (somente para compressão)
        self.header_label = tk.Label(root, text="Header (somente para compressão):")
        self.header_entry = tk.Entry(root, textvariable=self.header_path_var, width=50)
        self.header_browse_button = tk.Button(root, text="Browse", command=self.browse_header)

        # Widgets para opções de descompressão
        self.decompress_individual_rb = tk.Radiobutton(root, text="Individual", variable=self.decompress_mode, value=1)
        self.decompress_multiple_rb = tk.Radiobutton(root, text="Múltiplos", variable=self.decompress_mode, value=2)

        # Botão de execução
        tk.Button(root, text="Executar", command=self.execute).grid(row=4, column=1, pady=5)

        # Inicializa a UI
        self.update_ui()

    def browse_file(self):
        if self.mode.get() == 1:
            if self.decompress_mode.get() == 2:
                file_or_folder_path = filedialog.askdirectory(title="Escolha uma pasta")
            else:
                file_or_folder_path = filedialog.askopenfilename(title="Escolha um arquivo")
        else:
            file_or_folder_path = filedialog.askopenfilename(title="Escolha um arquivo")
        self.file_path_var.set(file_or_folder_path)

    def browse_header(self):
        header_path = filedialog.askopenfilename(title="Escolha um arquivo de cabeçalho")
        self.header_path_var.set(header_path)

    def update_ui(self):
        # Remove widgets antigos
        for widget in self.root.grid_slaves():
            widget.grid_forget()

        # Redefine os widgets
        tk.Label(self.root, text="Modo:").grid(row=0, column=0, pady=5)
        self.decompress_rb.grid(row=0, column=1, padx=5)
        self.compress_rb.grid(row=0, column=2, padx=5)

        if self.mode.get() == 1:  # Descompressão
            self.file_label.grid(row=1, column=0, pady=5)
            self.file_entry.grid(row=1, column=1, padx=5)
            self.browse_file_button.grid(row=1, column=2, padx=5)
            tk.Label(self.root, text="Descomprimir:").grid(row=2, column=0, pady=5)
            self.decompress_individual_rb.grid(row=2, column=1, padx=5)
            self.decompress_multiple_rb.grid(row=2, column=2, padx=5)
        else:  # Compressão
            self.file_label.grid(row=1, column=0, pady=5)
            self.file_entry.grid(row=1, column=1, padx=5)
            self.browse_file_button.grid(row=1, column=2, padx=5)
            self.header_label.grid(row=2, column=0, pady=5)
            self.header_entry.grid(row=2, column=1, padx=5)
            self.header_browse_button.grid(row=2, column=2, padx=5)

        # Botão de execução
        tk.Button(self.root, text="Executar", command=self.execute).grid(row=3, column=1, pady=5)

    def execute(self):
        mode = self.mode.get()
        file_path = self.file_path_var.get()
        header_path = self.header_path_var.get()

        if not file_path:
            messagebox.showerror("Erro", "Nenhum arquivo ou pasta selecionado.")
            return

        try:
            if mode == 1:  # Descompressão
                if self.decompress_mode.get() == 2:
                    decompress_all_rle4_in_folder(file_path)
                    messagebox.showinfo("Sucesso", "Descompressão completa.\nTodos os arquivos .rle4 foram descomprimidos na pasta 'extracted'.")
                else:
                    header_file, output_file = decompress_tim(file_path)
                    messagebox.showinfo("Sucesso", f"Descompressão completa.\nArquivo de cabeçalho salvo em: {header_file}\nArquivo descomprimido salvo em: {output_file}")
            elif mode == 2:  # Compressão
                if not header_path:
                    messagebox.showerror("Erro", "Nenhum arquivo de cabeçalho selecionado.")
                    return
                output_file = compress_tim(file_path, header_path)
                messagebox.showinfo("Sucesso", f"Compressão completa.\nArquivo comprimido salvo em: {output_file}")
            else:
                messagebox.showerror("Erro", "Modo inválido selecionado.")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = CompressionApp(root)
    root.mainloop()
