#include <stdio.h>
#include <stdlib.h>
#include <conio.h>
#include <string.h>
#include <locale.h>
#include <direct.h>

#define EXIT(text) { printf(text); exit(EXIT_FAILURE); }

long contador(char* nome, unsigned int inicio, unsigned int Offset_fim);
void calcula_ponteiro(char* nome, unsigned int Offset_ini, unsigned int Offset_fim, unsigned int InicioPonteiro);
void Dumper(char* nome);
void Inserter(char* nome_trad);
void  Titulo(void);
void  ComoUsar(void);


/*----------------------------------------------------------------------------*/
int main(int argc, char** argv) {
	//.DoModal();
	int opc;

	setlocale(LC_ALL, "Portuguese");
	_mkdir("Original");
	_mkdir("Translated");

	Titulo();

	if (argc != 3) ComoUsar();

	if (!_strcmpi(argv[1], "-e")) Dumper(argv[2]);
	else if (!_strcmpi(argv[1], "-i")) Inserter(argv[2]);
	else                              EXIT("Parametro desconhecido \n");

	printf("\nRip...Done\n");

	exit(EXIT_SUCCESS);
}

/*----------------------------------------------------------------------------*/
void Titulo(void) {
	printf(
		"\n"
		"DUMP - Copyright (C) 2022 Luke\n"
		"MUPPET MONSTER ADVENTURE PSX\n"
		"\n"
	);
}

/*----------------------------------------------------------------------------*/
void ComoUsar(void) {
	EXIT(
		"How to use: DUMP -e|-i file_name.xxx\n"
		"\n"
		"-e ... extrair 'file_name.xxx' it will create two folders - 'Original' - 'Translated'\n"
		"-i ... insert 'file_name.xxx' do not forget to put the .txt file inside of 'Translated' folder\n"
	);
}

/*----------------------------------------------------------------------------*/

void Dumper(char* nome) {
	FILE* arquivo, * arquivo_saida;
	unsigned char* memoria;
	char saida[1000];
	char caminho_orig[1000] = "Original\\";
	int cont = 0;
	int contador = 0;
	long tamanho, entries, table;
	short tamanho_corrigido;
	long table2;
	long endpointer;
	long endstring;
	long lastpointer;
	long first;
	long soma_end;
	long check;
	long adjust;
	unsigned int offset_ini, i, end_ponteiro;

	arquivo = fopen(nome, "rb");

	fseek(arquivo, 0, SEEK_END);
	tamanho = ftell(arquivo);

	fseek(arquivo, 2, SEEK_SET);
	fread(&entries, sizeof(long), 1, arquivo);
	endpointer = entries * 8;
	fseek(arquivo, endpointer - 4, SEEK_SET);
	fread(&lastpointer, sizeof(long), 1, arquivo);



	fseek(arquivo, SEEK_SET + 0x02, SEEK_SET);
	fread(&table, sizeof(long), 1, arquivo);
	table2 = table * 9 + 4;

	soma_end = lastpointer + table2;
	adjust = tamanho - soma_end;

	endstring = soma_end + adjust;


	printf("Size: %.8X\n", tamanho);
	printf("Entries: %d\n", entries);
	printf("Text_Begin: %x\n", table2);
	printf("Text_End: %X", endstring);
	//getch();

	fseek(arquivo, 0, SEEK_SET);
	memoria = (unsigned char*)malloc(sizeof(unsigned char) * tamanho);
	cont = fread(memoria, sizeof(unsigned char), tamanho, arquivo);
	fclose(arquivo);

	strcpy(saida, nome);
	strcat(saida, ".txt");
	strcat(caminho_orig, saida);

	arquivo_saida = fopen(caminho_orig, "wt");

	for (i = table2; i <= endstring; i++) {
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

	printf("\nScript extracted!\n");
	//getch();

	fclose(arquivo_saida);
	free(memoria);
}

void Inserter(char* nome_trad) {
	FILE* arq, * out;
	char s[1000];
	int cont = 0;
	long cont_letras, char_cont_ant, soma, tamanho, table;
	short tamanho_corrigido;
	unsigned int c;
	unsigned int Offset_ini;
	unsigned int Offset_fim;
	unsigned int ponteiro_mod, ponteiro_ant;
	unsigned int ponteiro_orig;

	int i;
	char caminho_orig[50] = "Original\\";
	char caminho_trad[50] = "Translated\\";

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

	fseek(out, SEEK_SET + 0x02, SEEK_SET);
	fread(&table, sizeof(long), 1, out);
	Offset_ini = table * 9 + 4;

	fseek(out, Offset_ini, SEEK_SET);
	printf("\nInserting...\n");

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

	Offset_fim = Offset_fim - 0;

	fclose(arq);
	fclose(out);

	calcula_ponteiro(nome_trad, Offset_ini, Offset_fim, 0x0C);

	printf("Script inserted!\nPress any key to continue.");
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
	short ajuste;
	short endpointer;
	short voltar;
	short first = 0x0000;
	long checkpointer;

	arquivo_mod = fopen(nome, "r+b");

	fseek(arquivo_mod, 2, SEEK_SET);
	fread(&ajuste, sizeof(short), 1, arquivo_mod);
	endpointer = ajuste * 9 + 2;
	checkpointer = ajuste * 8 + 4;
	fseek(arquivo_mod, endpointer, SEEK_SET);
	fread(&voltar, sizeof(short), 1, arquivo_mod);
	fseek(arquivo_mod, endpointer, SEEK_SET);
	fwrite(&first, sizeof(short), 1, arquivo_mod);



	fseek(arquivo_mod, 0, SEEK_SET);

	memoria_mod = (unsigned char*)malloc(sizeof(unsigned char) * Offset_fim);
	cont = fread(memoria_mod, sizeof(unsigned char), Offset_fim, arquivo_mod);
	k = InicioPonteiro;


	for (i = Offset_ini; k < Offset_ini; i++) {
		
		if (k == checkpointer) {
			break;
		}


		if (k == 0x04) {
			soma = 0;
			cont_letras = cont_letras = contador(nome, i, Offset_fim);
			cont_letras = cont_letras + 1;

			fseek(arquivo_mod, SEEK_SET + k, SEEK_SET);

			calculo_ponteiro1 = soma;
			calculo_ponteiro2 = cont_letras;

			PonteiroByte1 = (unsigned char)(calculo_ponteiro1 & 0x000000FF);
			PonteiroByte2 = (unsigned char)((calculo_ponteiro1 >> 8) & 0x000000FF);

			fwrite(&PonteiroByte1, sizeof(unsigned char), 1, arquivo_mod);
			fwrite(&PonteiroByte2, sizeof(unsigned char), 1, arquivo_mod);
			
			   k = k + 8;
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

			k = k + 8;


		}

	}
	fseek(arquivo_mod, endpointer, SEEK_SET);
	fwrite(&voltar, sizeof(short), 1, arquivo_mod);
	fclose(arquivo_mod);
	free(memoria_mod);
}


long contador(char* nome, unsigned int inicio, unsigned int Offset_fim) {
	FILE* arquivo_cont;
	int cont;
	unsigned char* memoria_cont;
	int cont_mod = 0;
	unsigned int i;
	long contagem = 0x00;

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

