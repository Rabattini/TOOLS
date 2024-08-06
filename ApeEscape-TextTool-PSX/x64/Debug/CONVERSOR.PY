import os
import glob
import codecs

# Define o caminho para a pasta de entrada (UTF-8)
input_folder = "scripts_traduzidos"

# Define o codec para UTF-8
input_codec = "utf-8"

# Define o codec para ANSI
output_codec = "cp1252"

# Percorre todos os arquivos na pasta de entrada
for file_path in glob.glob(os.path.join(input_folder, "*.txt")):
    # Abre o arquivo de entrada com o codec UTF-8
    with codecs.open(file_path, "r", input_codec) as file_in:
        # Lê o conteúdo do arquivo de entrada em uma variável
        content = file_in.read()
    
    # Abre o arquivo de saída com o codec ANSI no mesmo caminho do arquivo de entrada
    with codecs.open(file_path, "w", output_codec) as file_out:
        # Escreve o conteúdo convertido para ANSI no arquivo de saída
        file_out.write(content)
