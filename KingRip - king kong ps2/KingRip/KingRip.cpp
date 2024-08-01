#define _CRT_SECURE_NO_WARNINGS

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
#include <vector>
#include <algorithm>
#include <io.h>

using namespace std;


#define EXIT(text) { printf(text); exit(EXIT_FAILURE); }


long contador(char* nome, unsigned int inicio, unsigned int Offset_fim);
void calcula_ponteiro(char* nome, unsigned int Offset_ini, unsigned int Offset_fim, unsigned int InicioPonteiro);
void Dumper(char* nome, unsigned int Offset_user);
void Inserter(char* nome_trad, unsigned int Offset_user);
void  Titulo(void);
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

	if (argc != 4) ComoUsar();

	if (!_strcmpi(argv[1], "-e")) {
		char* nome = argv[2];
		unsigned int offset_user = (unsigned int)strtol(argv[3], NULL, 0);
		Dumper(nome, offset_user);
	}
	else if (!_strcmpi(argv[1], "-i")) {
		char* nome = argv[2];
		unsigned int offset_user = (unsigned int)strtol(argv[3], NULL, 0);
		Inserter(nome, offset_user);
	}
	else {
		EXIT("Parametro desconhecido \n");
	}

	printf("\nRip...Feito\n");

	exit(EXIT_SUCCESS);
}

/*----------------------------------------------------------------------------*/
void Titulo(void) {
	printf(
		"\n"
		"DUMP - Copyright (C) 2023 Luke\n"
		"KING KONG RIP PS2\n"
		"\n"
	);
}

/*----------------------------------------------------------------------------*/
void ComoUsar(void) {
	EXIT(
		"Como Usar: DUMP -e|-i Nome do arquivo.xxx\n"
		"\n"
		"-e ... extrair 'nome do arquivo.xxx' irá criar duas pastas - scripts_originais - scripts_traduzidos\n"
		"-i ... insert 'nome do arquivo.xxx' não esqueça de colocar o .txt traduzido dentro da pasta 'scripts_traduzidos' \n"
	);
}

/*----------------------------------------------------------------------------*/

void Dumper(char* nome, unsigned int Offset_user)
{

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


	FILE* arquivo, * arquivo_saida;
	unsigned char* memoria;
	char saida[50];
	char caminho_orig[50] = "scripts_originais\\";
	int cont = 0;
	int contador = 0;
	long tamanho;
	long endstring;
	long begin;
	
	unsigned int offset_ini, i, end_ponteiro;

	arquivo = fopen(nome, "rb");

	fseek(arquivo, 0, SEEK_END);
	tamanho = ftell(arquivo);

	fseek(arquivo, Offset_user, SEEK_SET);
	const unsigned int patternSize = 4;
	unsigned char searchPattern[patternSize] = { 0x2E, 0x74, 0x78, 0x6c };

	unsigned char buffer[patternSize];
	bool found = false;
	while (fread(buffer, patternSize, 1, arquivo) == 1 && !found) {
		if (memcmp(buffer, searchPattern, patternSize) == 0) {
			endstring = ftell(arquivo) - patternSize;
			found = true;
		}
		else {
			// Desloca 1 byte e tenta novamente
			fseek(arquivo, -3, SEEK_CUR);
		}
	}
	if (!found) {
		// a ocorrência não foi encontrada, define a posição do final da string como o tamanho do arquivo
		fseek(arquivo, 0, SEEK_END);
		endstring = ftell(arquivo) + 8;
	}
	

	//fclose(arquivo);
	

	begin = Offset_user;

	endstring = endstring -8;

	printf("Tamanho: %.8X\n", tamanho);
	printf("Beginstring: %x\n", begin);
	//printf("Table: %x\n", table2);
	//printf("Offset_ini: %X\n", offset_ini);
	printf("Endstring: %X\n", endstring);
	//printf("EndPointer: %X", endpointer);
	//getch();
	//return;

	fseek(arquivo, 0, SEEK_SET);
	memoria = (unsigned char*)malloc(sizeof(unsigned char) * tamanho);
	cont = fread(memoria, sizeof(unsigned char), tamanho, arquivo);
	fclose(arquivo);
	int index = 0;
	char indexStr[4] = "";
	strcpy(saida, nome);
	char pasta_saida[100] = "scripts_originais\\";

	while (true) {
		// redefine a string saida a cada iteração
		char caminho_saida[100] = "";
		sprintf(indexStr, "_%02d", index);
		strcpy(caminho_saida, pasta_saida);
		strcat(caminho_saida, saida);
		strcat(caminho_saida, indexStr);
		strcat(caminho_saida, ".txt");

		// verifica se o arquivo de saída existe
		arquivo_saida = fopen(caminho_saida, "r");
		if (arquivo_saida == NULL) {
			arquivo_saida = fopen(caminho_saida, "wt");
			strcat(saida, indexStr);
			strcat(saida, ".txt");
			break;
		}
		fclose(arquivo_saida);

		// incrementa o índice
		index++;
	}




	//arquivo_saida = fopen(caminho_orig, "wt");

	for (i = begin; i <= endstring; i++) {
		if (memoria[i] == 0x0a) {
			fprintf(arquivo_saida, "{%.2x}\n", memoria[i]);

		}
		if (memoria[i] == 0x00) {
			fprintf(arquivo_saida, "{%.2x}\n------------\n", memoria[i]);
		}
		else {
			fprintf(arquivo_saida, "%c", memoria[i]);

		}
	}

	printf("\nScript Dumpado com êxito!\n");
	//getch();

	fclose(arquivo_saida);
	free(memoria);
	//delete[] buffer;
	
}

void Inserter(char* nome_trad, unsigned int Offset_user) {

	map<string, int> tabEntry;
	map<string, int>::iterator it;

	//tabela hardcoded, já coloca em hex direto
	tabEntry.insert(pair<string, int>("a", 0x10));
	tabEntry.insert(pair<string, int>("b", 0x11));
	tabEntry.insert(pair<string, int>("c", 0x12));
	tabEntry.insert(pair<string, int>("d", 0x13));

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
	unsigned int ponteiro_mod, ponteiro_ant;
	unsigned int ponteiro_orig;
	unsigned int loch;
	unsigned int loci;
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
	char caminho_orig[50] = "scripts_originais\\";
	char caminho_trad[50] = "scripts_traduzidos\\";

	strcat(caminho_orig, nome_trad);
	strcat(caminho_trad, nome_trad);

	strcat(caminho_orig, ".txt");
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

	//ACHAR PRIMEIRO PONTEIRO
	fseek(out, Offset_user, SEEK_SET);

	const unsigned int patternSize = 4;
	unsigned char searchPattern[patternSize] = { 0x2E, 0x74, 0x78, 0x6c };

	unsigned char buffer[patternSize];
	bool found = false;
	long pos = ftell(out);

	while (pos > 0 && !found) {
		long readSize = pos < patternSize ? pos : patternSize;
		fseek(out, pos - readSize, SEEK_SET);
		fread(buffer, readSize, 1, out);
		for (int i = readSize - 1; i >= 0; i--) {
			if (buffer[i] == searchPattern[readSize - 1]) {
				bool match = true;
				for (int j = readSize - 2; j >= 0; j--) {
					if (buffer[i - readSize + j + 1] != searchPattern[j]) {
						match = false;
						break;
					}
				}
				if (match) {
					pointer = pos - readSize + i+0x29;
					found = true;
					break;
				}
			}
		}
		pos -= readSize;
	}

	if (!found) {
		fseek(out, 0, SEEK_END);
		pointer = ftell(out) + 8;
	}
	printf("Posição do primeiro ponteiro: %lx\n", pointer);
	//return;

	//ACHAR FINAL DA STRING
	fseek(out, Offset_user, SEEK_SET);
	const unsigned int patternSize2 = 4;
	unsigned char searchPattern2[patternSize2] = { 0x2E, 0x74, 0x78, 0x6c };
	

	unsigned char buffer2[patternSize2];
	bool found2 = false;
	while (fread(buffer2, patternSize2, 1, out) == 1 && !found2) {
		if (memcmp(buffer2, searchPattern2, patternSize2) == 0) {
			endstring2 = ftell(out) - patternSize2-9;
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
					i = i + 3;
				}
			}
			else {
				c = s[i];
				fwrite(&c, sizeof(unsigned char), 1, out);
			}
		}
	}

	Offset_fim = ftell(out);

	Offset_fim = Offset_fim - 1;

	UINT oldcodepage = GetConsoleOutputCP();
	SetConsoleOutputCP(65001);
	checksize = endstring2;
	warning = (Offset_fim - checksize);
	if (Offset_fim > checksize) {
		printf("Excedeu o bloco por: %.4X\n", warning);
		printf("Isso pode causar problemas no jogo, por favor teste antes de usar\n");

	}

	checksize = endstring2;
	warning = (Offset_fim - checksize);
	if (Offset_fim < checksize) {
		printf("O tamanho do bloco é: %.4X\n", warning);
		printf("Seu texto é menor do que o original, então está tudo bem\nCalculando, por favor aguarde...\n");

	}
	
	

	fclose(arq);
	fclose(out);

	calcula_ponteiro(nome_trad, Offset_user, Offset_fim, pointer);

	printf("Script Inserido com sucesso!\nPressione qualquer tecla para continuar.");

	//getch();
}


void calcula_ponteiro(char* nome, unsigned int Offset_ini, unsigned int Offset_fim, unsigned int InicioPonteiro) {

	FILE* arquivo_mod;
	unsigned char* memoria_mod;
	unsigned char PonteiroByte1, PonteiroByte2, PonteiroByte3, PonteiroByte4;
	unsigned int i;
	unsigned int k = 0;
	int cont;
	unsigned int cont_letras = 0;
	unsigned int soma;
	unsigned int char_cont_ant = 0x00;
	long char_cont;
	long calculo_ponteiro1, calculo_ponteiro2;
	long table;

	arquivo_mod = fopen(nome, "r+b");

	fseek(arquivo_mod, 0, SEEK_SET);

	memoria_mod = (unsigned char*)malloc(sizeof(unsigned char) * Offset_fim);
	cont = fread(memoria_mod, sizeof(unsigned char), Offset_fim, arquivo_mod);
	k = InicioPonteiro;

	for (i = Offset_ini; k < Offset_ini; i++) {

		if (k == 0x04) {
			soma = 0;
			cont_letras = cont_letras = contador(nome, i, Offset_fim);
			cont_letras = cont_letras + 1;

			fseek(arquivo_mod, SEEK_SET + k, SEEK_SET);

			calculo_ponteiro1 = soma;
			calculo_ponteiro2 = cont_letras;

			PonteiroByte1 = (unsigned char)(calculo_ponteiro1 & 0x000000FF);
			PonteiroByte2 = (unsigned char)((calculo_ponteiro1 >> 8) & 0x000000FF);

			PonteiroByte3 = (unsigned char)(calculo_ponteiro2 & 0x000000FF);
			PonteiroByte4 = (unsigned char)((calculo_ponteiro2 >> 8) & 0x000000FF);

			fwrite(&PonteiroByte1, sizeof(unsigned char), 1, arquivo_mod);
			fwrite(&PonteiroByte2, sizeof(unsigned char), 1, arquivo_mod);

			k = k + 24;
		}

		if (memoria_mod[i - 1] == 0x00) {

			//Para obter o ponteiro
			cont_letras = contador(nome, i, Offset_fim);
			cont_letras = cont_letras + 1;

			soma = char_cont_ant + cont_letras;

			//Para obter o próximo char_cont
			cont_letras = contador(nome, i + cont_letras, Offset_fim);
			cont_letras = cont_letras + 1;

			fseek(arquivo_mod, SEEK_SET + k, SEEK_SET);

			calculo_ponteiro1 = soma;
			calculo_ponteiro2 = cont_letras;

			PonteiroByte1 = (unsigned char)(calculo_ponteiro1 & 0x000000FF);
			PonteiroByte2 = (unsigned char)((calculo_ponteiro1 >> 8) & 0x000000FF);

			PonteiroByte3 = (unsigned char)(calculo_ponteiro2 & 0x000000FF);
			PonteiroByte4 = (unsigned char)((calculo_ponteiro2 >> 8) & 0x000000FF);

			fwrite(&PonteiroByte1, sizeof(unsigned char), 1, arquivo_mod);
			fwrite(&PonteiroByte2, sizeof(unsigned char), 1, arquivo_mod);

			char_cont_ant = soma;
			cont_letras = 0;

			k = k + 24;
		}
	}
	fclose(arquivo_mod);
	free(memoria_mod);
}


long contador(char* nome, unsigned int inicio, unsigned int Offset_fim) {
	FILE* arquivo_cont;
	int cont;
	unsigned char* memoria_cont;
	int cont_mod = 0;
	unsigned int i;
	long contagem = 0;

	arquivo_cont = fopen(nome, "r+b");
	fseek(arquivo_cont, 0, SEEK_SET);

	memoria_cont = (unsigned char*)malloc(sizeof(unsigned char) * Offset_fim);
	cont = fread(memoria_cont, sizeof(unsigned char), Offset_fim, arquivo_cont);

	for (i = inicio; memoria_cont[i] != 0x00; i++) {
		contagem++;
	}

	fclose(arquivo_cont);
	free(memoria_cont);
	return contagem;



}
