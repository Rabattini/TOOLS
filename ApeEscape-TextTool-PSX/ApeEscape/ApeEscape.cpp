#define _CRT_SECURE_NO_WARNINGS
#define _SILENCE_CXX17_CODECVT_HEADER_DEPRECATION_WARNING

#include <iostream>
#include <stdio.h>
#include <stdlib.h>
#include <conio.h>
#include <string.h>
#include <locale.h>
#include <direct.h>
#include <windows.h>
#include <fstream>
#include <map>
#include <string>
#include <sstream>
#include <dirent.h>
#include <iconv.h>
#include <codecvt>
#include <clocale>
#include <filesystem>
#include <vector>



using namespace std;


#define EXIT(text) { printf(text); exit(EXIT_FAILURE); }


long contador(char* nome, unsigned int inicio, unsigned int Offset_fim);
void calcula_ponteiro(char* nome, unsigned int Offset_ini, unsigned int Offset_fim, unsigned int InicioPonteiro, unsigned int char_cont_ant2);
void Dumper(char* nome);
void Inserter(char* nome_trad, unsigned int Offset_user, unsigned int id);
void  Titulo(void);
void  Ansiconverter(void);
void  ComoUsar(void);


/*----------------------------------------------------------------------------*/
int main(int argc, char** argv) {

	int opc;

	//setlocale(LC_ALL, "Portuguese");
	UINT CPAGE_UTF8 = 65001;
	SetConsoleOutputCP(CPAGE_UTF8);
	_mkdir("scripts_originais");
	_mkdir("scripts_traduzidos");

	Titulo();

	if (argc != 3 && argc != 5) ComoUsar();
	if (!_strcmpi(argv[1], "-c")) Ansiconverter();
	if (!_strcmpi(argv[1], "-e")) Dumper(argv[2]);
	else if (!_strcmpi(argv[1], "-i")) {
		char* nome = argv[2];
		unsigned int offset_user = (unsigned int)strtol(argv[3], NULL, 0);
		unsigned int id = (unsigned int)strtol(argv[4], NULL, 0);
		Inserter(nome, offset_user, id);
		
	}
	else {
		EXIT("Parametro desconhecido \n");
	}
	// Chamando a função Ansiconverter()
	
	printf("\nRip...Feito\n");

	exit(EXIT_SUCCESS);


}

/*----------------------------------------------------------------------------*/
void Titulo(void) {
	printf(
		"\n"
		"DUMP - Copyright (C) 2023 Luke\n"
		"APE ESCAPE PSX\n"
		"\n"
	);
}

/*----------------------------------------------------------------------------*/
void ComoUsar(void) {
	EXIT(
		"Como Usar: DUMP -e|-i Nome do arquivo.xxx\n"
		"\n"
		"-e ... extrair 'nome do arquivo.xxx' irá criar duas pastas - scripts_originais - scripts_traduzidos\n"
		"-i ... insert 'nome do arquivo.xxx' Offset do inicio do texto e id do texto não esqueça de colocar o .txt traduzido dentro da pasta 'scripts_traduzidos' \n"
		"Exemplo programa.exe nomedoarquivo.xxx 0x7000 3"
	);
}

/*----------------------------------------------------------------------------*/
void Ansiconverter() {

	// Define o caminho para a pasta de entrada (UTF-8)
	std::string input_folder = "scripts_traduzidos";

	// Define o codec para UTF-8
	std::string input_codec = "UTF-8";

	// Define o codec para ANSI
	std::string output_codec = "CP1252";

	// Lista todos os arquivos na pasta de entrada e seus subdiretórios
	for (auto& entry : std::filesystem::recursive_directory_iterator(input_folder)) {
		if (entry.is_regular_file()) {
			try {
				// Abre o arquivo de entrada com o codec UTF-8
				std::ifstream file_in(entry.path(), std::ios::binary);
				std::stringstream buffer_in;
				buffer_in << file_in.rdbuf();
				std::string content_in = buffer_in.str();

				// Converte a string de entrada para ANSI
				std::wstring_convert<std::codecvt_utf8_utf16<wchar_t>> converter;
				std::wstring content_wstr = converter.from_bytes(content_in);
				std::string content_out = std::wstring_convert<std::codecvt<wchar_t, char, std::mbstate_t>>().to_bytes(content_wstr);

				// Abre o arquivo de saída com o codec ANSI no mesmo caminho do arquivo de entrada
				std::ofstream file_out(entry.path(), std::ios::binary);
				file_out << content_out;
				std::cerr << "O arquivo está em UTF8 " << entry.path() << "CONVERTER!" << std::endl;
			}
			catch (const std::exception& ex) {
				std::cerr << "O arquivo está em ANSI " << entry.path() << "OK!" << std::endl;
			}
		}
	}
}
void Dumper(char* nome) {

	map<int, string> tabEntry;
	map<int, string>::iterator it;

	//tabela hardcoded, já coloca em hex direto
	tabEntry.insert(pair<int, string>(0x10, "a"));
	tabEntry.insert(pair<int, string>(0x11, "b"));
	tabEntry.insert(pair<int, string>(0x12, "c"));
	tabEntry.insert(pair<int, string>(0x13, "d"));

	//tabela do arquivo, precisa ler e converter para hex
	ifstream fp("tabela.tbl");
	string line;
	string valHex, valChar;
	int hexValue;

	//apaga as letras hardcoded de antes
	tabEntry.clear();

	if (fp.is_open()) {

		while (getline(fp, line)) {

			stringstream ss(line);

			if (!getline(ss, valHex, '=') || !getline(ss, valChar)) {
				cout << "tabela com erro!" << endl;
				return;
			}

			stringstream sshex;
			sshex << hex << valHex;
			sshex >> hexValue;

			tabEntry.insert(pair<int, string>(hexValue, valChar));

		}
		fp.close();
	}
	else {
		cout << "Erro ao ler arquivo!" << endl;
		return;
	}
	FILE* arquivo_hed;
	arquivo_hed = fopen("KKIIDDZZ.HED", "rb");
	unsigned short begin_text;
	int begin_final;
	unsigned short end_text;
	int end_final;
	fseek(arquivo_hed, 0, SEEK_END);
	fseek(arquivo_hed, 0x50, SEEK_SET);
	

	fread(&begin_text, sizeof(unsigned short), 1, arquivo_hed);
	printf("check_begin: %.8X\n", begin_text);
	begin_final = begin_text * 0x800;
	printf("Begin: %.8X\n", begin_final);

	fread(&end_text, sizeof(unsigned short), 1, arquivo_hed);
	printf("check_end: %.8X\n", end_text);
	end_final = end_text * 0x80 + begin_final;
	printf("End: %.8X\n", end_final);
	
	FILE* arquivo, * arquivo_saida;
	unsigned char* memoria;
	char saida[50];
	char caminho_orig[50] = "scripts_originais\\";
	int cont = 0;
	int contador = 0;
	int tamanho, entries, table;

	long endstring;
	long begin;
	unsigned int offset_ini, i, end_ponteiro;

	arquivo = fopen(nome, "rb");

	fseek(arquivo, 0, SEEK_END);
	fseek(arquivo, 0, SEEK_SET);
	
	// Procurar pelos bytes 0x0b 0x01 e extrair até achar 0x00000000
	int start = 0;
	int end = 0;
	int posicao = begin_final; // Armazena a posição atual
	
	int fileNum = 1; // número do arquivo de saída
	tamanho = end_final;

	fseek(arquivo, 0, SEEK_SET);
	memoria = (unsigned char*)malloc(sizeof(unsigned char) * tamanho);
	cont = fread(memoria, sizeof(unsigned char), tamanho, arquivo);
	fclose(arquivo);
	bool found = true; // Começa procurando desde o início do arquivo
	printf("Posicao: %.4X\n", posicao);
	printf("Tamanho: %.4X\n", tamanho);
	

	while (posicao < tamanho) { // Enquanto não chegou ao final do arquivo
		int start = posicao; // Inicia a busca a partir da posição atual
		int end = end_final-1; // Armazena o fim da extração

		// Procura pelo final do script
		while (posicao < tamanho) {
			if (memoria[posicao] == 0x00 && memoria[posicao + 1] == 0x00 && memoria[posicao + 2] == 0x00) {
				end = posicao; // Armazena a posição do fim da extração
				break;
			}
			posicao++;
		}

		if (end == 0) { // Não encontrou o final do script
			break;
		}

		// Copia o texto encontrado para o arquivo de saída
		sprintf(saida, "%s%d.txt", nome, fileNum++);
		strcpy(caminho_orig, "scripts_originais\\");
		strcat(caminho_orig, saida);
		
		std::setlocale(LC_ALL, "C/LC_CTYPE");
		FILE* arquivo_saida = fopen(caminho_orig, "wt");

		if (arquivo_saida == NULL) {
			printf("Erro ao criar arquivo de saída!\n");
			return;
		}
		for (int j = start; j < end; j++) {
			if (memoria[j] == 0x0d) {
				fprintf(arquivo_saida, "{%.2x}\n", memoria[j]);
			}
			else if (memoria[j] == 0x01) {
				fprintf(arquivo_saida, "{%.2x}\n------------\n", memoria[j]);
			}
			else {
				it = tabEntry.find(memoria[j]);
				if (it != tabEntry.end()) {
					fprintf(arquivo_saida, "%s", it->second.c_str());
					//const char* buffer = it->second.c_str();
					//fwrite(buffer, 1, strlen(buffer), arquivo_saida);

				}
				else {
					fprintf(arquivo_saida, "{%.2x}", memoria[j]);
				}
			}
		}

		// Fecha o arquivo e o conversor
		fclose(arquivo_saida);
		

		//fclose(arquivo_saida);

		// Atualiza a posição atual para começar a buscar o próximo script
		posicao = start + 0x800;
	}

	// Se não encontrou nenhuma ocorrência de 0x00000000, avisa o usuário
	if (fileNum == 1) {
		printf("Nenhum script encontrado no arquivo %s!\n", nome);
	}
	else {
		printf("\nForam criados %d arquivos de saída!\n", fileNum - 1);
	}


	// abre o arquivo insertor.bat para escrita
	ofstream batFile("insertor.bat");

	if (batFile.is_open()) {
		int posicao = begin_final; // inicializa a posição atual como zero

		// escreve o comando do primeiro arquivo no arquivo insertor.bat
		sprintf(saida, "%s%d.txt", nome, 1);
		batFile << "ApeEscape.exe -c " << nome << endl;
		batFile << "ApeEscape.exe -i " << nome << " " << posicao << " 1" << endl;
		

		// loop de gravação dos arquivos de saída a partir do segundo arquivo
		for (int i = 2; i <= fileNum; i++) {
			// incrementa a posição atual em 0x800 para o próximo arquivo
			posicao += 0x800;

			// cria o nome do arquivo de saída
			sprintf(saida, "%s%d.txt", nome, i);

			// escreve o comando no arquivo insertor.bat
			batFile << "ApeEscape.exe -i " << nome << " " << posicao << " " << i << endl;
		}

		// fecha o arquivo insertor.bat
		batFile.close();

		printf("\nArquivo insertor.bat criado com êxito!\n");
	}
	else {
		printf("\nErro ao criar arquivo insertor.bat!\n");
	}



	free(memoria);

	printf("\nScript(s) dumpado(s) com êxito!\n");

	
}

void Inserter(char* nome_trad, unsigned int Offset_user, unsigned int id) {

	map<string, int> tabEntry;
	map<string, int>::iterator it;

	//tabela hardcoded, já coloca em hex direto
	//tabEntry.insert(pair<string, int>("a", 0x10));
	//tabEntry.insert(pair<string, int>("b", 0x11));
	//tabEntry.insert(pair<string, int>("c", 0x12));
	tabEntry.insert(pair<string, int>("á", 0xA0));
	tabEntry.insert(pair<string, int>(" ", 0xff));

	//tabela do arquivo, precisa ler e converter para hex
	ifstream fp("tabela.tbl");
	string line;
	string valHex, valChar;
	int hexValue;

	//apaga as letras hardcoded de antes
	//tabEntry.clear();

	if (fp.is_open()) {

		while (getline(fp, line)) {

			stringstream ss(line);

			if (!getline(ss, valHex, '=') || !getline(ss, valChar)) {
				cout << "tabela com erro!" << endl;

			}

			stringstream sshex;
			sshex << hex << valHex;
			sshex >> hexValue;

			tabEntry.insert(pair<string, int>(valChar, hexValue));

		}
		fp.close();
	}
	else {
		cout << "Erro ao ler arquivo!" << endl;

	}

	
	FILE* arq, * out;
	char s[10000];
	int cont = 0;
	long cont_letras, char_cont_ant, soma, tamanho, table;
	short tamanho_corrigido;
	unsigned int c;
	unsigned int Offset_ini;
	unsigned int Offset_fim;
	unsigned int pointer = 0;
	unsigned int checksize;
	unsigned int warning;
	unsigned int endstring;
	unsigned int begin;
	unsigned int char_cont_ant2;
	long begin2;
	int pointer_begin;
	unsigned int endstring2;

	int i;
	char caminho_orig[250] = "scripts_originais\\";
	char caminho_trad[250] = "scripts_traduzidos\\";
	// Tamanho máximo para caminho_orig e caminho_trad

	char id_str[20];
	sprintf(id_str, "%d", id);
	
	//strcat(caminho_orig, nome_trad);
	//strcat(caminho_trad, nome_trad);

	sprintf(id_str, "%d", id);
	strcat(caminho_orig, nome_trad);
	strcat(caminho_orig, id_str);
	strcat(caminho_orig, ".txt");

	sprintf(id_str, "%d", id);
	strcat(caminho_trad, nome_trad);
	strcat(caminho_trad, id_str);
	strcat(caminho_trad, ".txt");


	printf("Caminho original: %s\n\n", caminho_orig);
	printf("Caminho traduzido: %s\n\n", caminho_trad);

	if ((arq = fopen(caminho_trad, "r")) == NULL) {
		printf("Erro na abertura do arquivo modificado!\n\n");
		exit(0);
	}
	if ((out = fopen(nome_trad, "r+b")) == NULL) {
		printf("Erro na criação do arquivo de saída!\n");
		exit(0);
	}

	fseek(out, 0, SEEK_END);
	tamanho = ftell(out);
	
	//ACHAR FINAL DA STRING
	fseek(out, Offset_user, SEEK_SET);
	const unsigned int patternSize2 = 4;
	unsigned char searchPattern2[patternSize2] = { 0x00, 0x00, 0x00, 0x00 };


	unsigned char buffer2[patternSize2];
	bool found2 = false;
	while (fread(buffer2, patternSize2, 1, out) == 1 && !found2) {
		if (memcmp(buffer2, searchPattern2, patternSize2) == 0) {
			endstring2 = ftell(out) - patternSize2;
			found2 = true;
		}
		else {
			// Desloca 1 byte e tenta novamente
			fseek(out, -3, SEEK_CUR);
		}
	}
	if (!found2) {
		// a ocorrência não foi encontrada, define a posição do final da string como o tamanho do out
		fseek(out, 0, SEEK_END);
		endstring2 = ftell(out);
	}

	printf("Posição do primeiro ponteiro: %lx\n", endstring2);
	//return;


	fseek(out, Offset_user, SEEK_SET);
	printf("\nInserindo...\n");



	while (fgets(s, 1000, arq) != NULL) {
		if (!strcmp(s, "------------\n") || !strcmp(s, "------------")) {
			continue;
		}

		for (i = 0; i < (int)strlen(s) - 1; i++) {
			if (s[i] == '{') {
				if (s[i + 3] == '}') {
					sscanf(&s[i + 1], "%xx", &c);
					fwrite(&c, sizeof(unsigned char), 1, out);
					//fwrite(&tabEntry[string(1, c)], sizeof(unsigned char), 1, out);
					i = i + 3;
				}
			}
			else {
				c = s[i];
				//fwrite(&c, sizeof(unsigned char), 1, out);
				fwrite(&tabEntry[string(1, c)], sizeof(unsigned char), 1, out);
			}
		}
	}
	
	Offset_fim = ftell(out);

	Offset_fim = Offset_fim - 1;

	UINT oldcodepage = GetConsoleOutputCP();
	SetConsoleOutputCP(65001);
	
	fclose(arq);
	fclose(out);

	

	printf("Script Inserido com sucesso!\nPressione qualquer tecla para continuar.");

	//getch();
}
