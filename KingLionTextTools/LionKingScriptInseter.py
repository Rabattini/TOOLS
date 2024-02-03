import tkinter as tk
import re
from tkinter import filedialog
import struct
import os

# Abrir diálogo para escolha do arquivo original
root = tk.Tk()
root.withdraw()
original_file_path = filedialog.askopenfilename(title="Escolha o arquivo binário original", filetypes=[("Arquivo original", "*.*")])

# Abrir diálogo para escolha do arquivo de saída
output_file_path = filedialog.asksaveasfilename(title="Escolha o local e nome para salvar o arquivo binário de saída", defaultextension=".bin", filetypes=[("Binary Files", "*.bin")])

# Abrir diálogo para escolha do arquivo de texto traduzido
modified_file_path = filedialog.askopenfilename(title="Escolha o arquivo de texto traduzido", filetypes=[("Text Files", "*.txt")])

# Ler os dados do arquivo original
with open(original_file_path, 'rb') as original_file:
    # Ler o cabeçalho do arquivo original
    header_data = original_file.read(4)
    if header_data != b'PFLL':
        print('Arquivo original não é válido')
    else:
        # Ler os ponteiros do cabeçalho original
        original_file_size = len(original_file.read())
        original_file.seek(4)
        original_ultimo_ponteiro = int.from_bytes(original_file.read(4), byteorder='little')
        original_unknow = int.from_bytes(original_file.read(4), byteorder='little')
        original_entradas = int.from_bytes(original_file.read(4), byteorder='little')
        original_primeito_ponteiro = int.from_bytes(original_file.read(2), byteorder='little')

        # Ler os dados do arquivo modificado
        with open(modified_file_path, "r", encoding="utf-8") as modified_file:
            modified_data = modified_file.read()

            # Remover linhas que começam com "Offset"
            modified_data = '\n'.join(line for line in modified_data.split('\n') if not line.startswith('Offset'))

            # Substituir todas as ocorrências de {0x??} por seus equivalentes em bytes
            for match in re.finditer(r'{0x([0-9a-fA-F]+)}', modified_data):
                hex_value = match.group(1)
                byte_value = bytes([int(hex_value, 16)])
                modified_data = modified_data.replace(match.group(0), byte_value.decode('utf-8'))

            # Substituir quebras de linha por 0x00
            modified_data = modified_data.replace('\n', '\x00')

        # Abrir o arquivo de saída para escrita
        with open(output_file_path, "wb") as output_file:
            # Escrever o cabeçalho no arquivo de saída
            output_file.write(b'PFLL')
            original_file.seek(4)
            output_file.write(original_ultimo_ponteiro.to_bytes(4, byteorder='little'))
            output_file.write(original_unknow.to_bytes(4, byteorder='little'))
            output_file.write(original_entradas.to_bytes(4, byteorder='little'))
            output_file.write(original_primeito_ponteiro.to_bytes(2, byteorder='little'))
            
            # Pular para a posição indicada pelo original_primeito_ponteiro
            output_file.seek(original_primeito_ponteiro - 1)

            # Escrever os dados do arquivo modificado no arquivo de saída
            output_file.write(modified_data.encode('ansi'))

print("Inserção concluída com sucesso")



import struct
import os

nome_arquivo = output_file_path
tamanho_arquivo = os.path.getsize(nome_arquivo)

def encontrar_proximo_zero(file):
    contagem = 0
    while True:
        byte = file.read(1)
        if byte == b'\x00':
            break
        if not byte:
            break  # Adicionando verificação para o final do arquivo
        contagem += 1
    return contagem

# Abra o arquivo binário para leitura em modo binário
with open(nome_arquivo, 'r+b') as file:
    # Crie um novo arquivo binário para escrita temporário
    with open('ponteiros.bin', 'wb') as output_file:
        # Defina a variável ponteiro_mestre para 0x24c
        ponteiro_mestre = 0x24c

        while True:
            # Vá para a offset em ponteiro_mestre no arquivo
            file.seek(ponteiro_mestre)

            # Leia os dados até encontrar 0x00 e some ponteiro_mestre com a contagem
            contagem = encontrar_proximo_zero(file)
            nova_posicao = ponteiro_mestre + contagem + 1

            # Escreva a nova posição no arquivo de saída
            output_file.write(struct.pack('<H', nova_posicao))

            # Atualize ponteiro_mestre para a nova posição
            ponteiro_mestre = nova_posicao

            # Verifique se ainda existem pares de 0x00 a serem encontrados
            if nova_posicao > tamanho_arquivo:
                break

# Agora, abra o arquivo 'teste.bin' para leitura e escrita em modo binário
with open(nome_arquivo, 'r+b') as file:
    # Vá para a offset 0x12 no arquivo
    file.seek(0x12)

    # Leia o conteúdo do arquivo 'ponteiros.bin'
    with open('ponteiros.bin', 'rb') as ponteiros_file:
        ponteiros_data = ponteiros_file.read()[:-2]

        # Escreva o conteúdo do arquivo 'ponteiros.bin' na offset 0x12 do arquivo 'teste.bin'
        file.write(ponteiros_data)

# Excluir o arquivo 'ponteiros.bin'
os.remove('ponteiros.bin')
