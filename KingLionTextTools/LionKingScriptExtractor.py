import tkinter as tk
from tkinter import filedialog

# Abrir diálogo para escolha do arquivo
root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename()

# Abrir o arquivo
with open(file_path, 'rb') as file:
    # Passo 1 a Passo 5: ler cabeçalho do arquivo
    idstring = file.read(4).decode('utf-8')
    if idstring != 'PFLL':
        print('Arquivo não é válido')
    else:
        file_size = len(file.read())
        file.seek(4)
        ultimo_ponteiro = int.from_bytes(file.read(4), byteorder='little')
        unknow = int.from_bytes(file.read(4), byteorder='little')
        entradas = int.from_bytes(file.read(4), byteorder='little')

        # Step 4: Converte os dados extraídos usando a tabela.tbl
        conversion_table = {}
        with open("tabela.tbl", "r") as f:
            for line in f:
                key, value = line.strip().split("=")
                try:
                    if key.startswith("[") and key.endswith("]"):
                        hex_values = key[1:-1].split()
                        if len(hex_values) != 2:
                            raise ValueError
                        hex_values = [int(h, 16) for h in hex_values]
                        hex_value = int.from_bytes(bytes(hex_values[::-1]), byteorder='big')
                    else:
                        hex_value = int(key, 16)
                    string_value = value
                    if value == "":
                        string_value = " "
                except ValueError:
                    print(f"Invalid hex value '{key}' for value '{value}'. Skipping...")
                    continue
                conversion_table[hex_value] = string_value

        # Variable to store the concatenated converted data
        concatenated_data = ""

        # Loop para cada entrada
        for rip in range(1, entradas + 1):
            offset = int.from_bytes(file.read(2), byteorder='little')
            pos_offset = file.tell()
            size = int.from_bytes(file.read(2), byteorder='little')

            if size > file_size:
                size = ultimo_ponteiro - offset
            else:
                size = size - offset

            # Add a line break before each Offset
            concatenated_data += f"\nOffset: {offset}, Size: {size}, ultimo_ponteiro: {ultimo_ponteiro}, Entradas: {entradas}\n"

            file.seek(pos_offset)
            file.seek(offset)
            extracted_data = file.read(size)

            # Step 4: Converte os dados extraídos usando a tabela.tbl
            converted_data = ""
            i = 0
            while i < len(extracted_data):
                byte = extracted_data[i]
                if byte == 0x00:
                    i += 1  # Skip 0x00
                else:
                    if i + 1 < len(extracted_data):
                        next_byte = extracted_data[i + 1]
                        two_byte_key = int.from_bytes(bytes([byte, next_byte]), byteorder='big')
                        if two_byte_key in conversion_table:
                            converted_data += conversion_table[two_byte_key]
                            i += 2
                        else:
                            # Display the original byte in curly braces if not found in the conversion table
                            converted_data += f"{{0x{byte:02X}}}" if byte not in conversion_table else conversion_table.get(byte, chr(byte))
                            i += 1
                    else:
                        # Display the original byte in curly braces if not found in the conversion table
                        converted_data += f"{{0x{byte:02X}}}" if byte not in conversion_table else conversion_table.get(byte, chr(byte))
                        i += 1

            # Concatenate the converted data
            concatenated_data += converted_data

            # Passo 15: voltar para o início da próxima entrada
            file.seek(pos_offset)  # pula 4 bytes para ir para a próxima entrada

        # Passo 14: criar um novo arquivo e escrever os dados extraídos
        with open("output.txt", "w", encoding="utf-8") as output_file:
            output_file.write(concatenated_data)

print("Arquivo processado com sucesso")
