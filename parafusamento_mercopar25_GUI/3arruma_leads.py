# -*- coding: utf-8 -*-
#
# Arquivo: relatorio_por_usuario.py
# Descrição: Script Python que lê um arquivo de leads, divide os dados por 'USUARIO APP',
# adiciona um hiperlink para WhatsApp com mensagem personalizada e salva em arquivos XLSX separados.

import pandas as pd
import os
import sys
import re
from urllib.parse import quote  # Importa para codificar o texto da URL

# --- CONFIGURAÇÕES DO ARQUIVO E COLUNAS ---
# Nome do seu arquivo XLSX original.
NOME_ARQUIVO = "papaleads_SCQQ0WYSR4WR_20251016143229.xlsx"
COLUNA_ALVO_SPLIT = "USUARIO APP"  # Coluna usada para dividir os relatórios
COLUNA_CELULAR = "CELULAR"  # Coluna usada para criar o link do WhatsApp
COLUNA_NOME = "NOME"  # Nova coluna para pegar o nome do contato
COLUNA_ORDENACAO = "AVALIACAO"  # Coluna usada para ordenar (decrescente)

# Colunas a serem removidas do relatório final.
COLUNAS_PARA_REMOVER = [
    "DATA LEITURA",
    "HORA LEITURA",
    "RD STATION",
    "TIPO",
    "CODIGO",
    "AUTORIZA RECEBER MATERIAL PROMOCIONAL"
]


def gerar_relatorios_usuarios():
    """Lê o arquivo, processa os dados e salva um relatório XLSX por usuário."""

    # 1. Verificação de Dependência e Arquivo
    try:
        # Lendo diretamente o arquivo XLSX (necessita 'openpyxl' instalado: pip install openpyxl)
        df = pd.read_excel(NOME_ARQUIVO)
    except ImportError:
        print("ERRO: O Pandas e/ou o Openpyxl não estão instalados. Instale com: pip install pandas openpyxl")
        sys.exit(1)
    except FileNotFoundError:
        print(f"ERRO: Arquivo '{NOME_ARQUIVO}' não encontrado.")
        sys.exit(1)
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
        sys.exit(1)

    # 2. Verificação das Colunas Essenciais
    colunas_essenciais = [COLUNA_ALVO_SPLIT, COLUNA_CELULAR, COLUNA_ORDENACAO, COLUNA_NOME]
    for col in colunas_essenciais:
        if col not in df.columns:
            print(f"ERRO: A coluna essencial '{col}' não foi encontrada na planilha.")
            print(f"Colunas disponíveis: {df.columns.tolist()}")
            sys.exit(1)

    # 3. Limpeza e Criação do Link do WhatsApp

    print("\n--- Processando Dados e Gerando Links do WhatsApp ---")

    # Preenche valores NaN nas colunas essenciais
    df[COLUNA_CELULAR] = df[COLUNA_CELULAR].fillna('')
    df[COLUNA_NOME] = df[COLUNA_NOME].fillna('Cliente')
    # Garantir que a coluna de usuário seja string para evitar problemas no filtro
    df[COLUNA_ALVO_SPLIT] = df[COLUNA_ALVO_SPLIT].astype(str).str.strip()

    def criar_link_whatsapp(row):
        """Limpa o número, remove o 3º dígito e retorna a URL com a mensagem personalizada."""
        celular = row[COLUNA_CELULAR]
        nome = (str(row[COLUNA_NOME]).split()[0]).lower().capitalize()  # Pega apenas o primeiro nome

        user_app = (row[COLUNA_ALVO_SPLIT]).lower().capitalize()  # <-- NOVO: Captura o nome do usuário/consultor

        # 1. Limpa o número de celular
        celular_original = str(celular)

        celular_limpo = re.sub(r'\D', '', celular_original)

        # O problema com o slice de remoção do último dígito ([:-1]) foi corrigido na iteração anterior
        # mas garantindo que ele não retorne:
        celular_limpo = celular_limpo[:-1]

        # O número deve ter no mínimo 8 dígitos para ser considerado válido
        if len(celular_limpo) < 8:
            return ""

        # 2. Remover o 3º dígito (índice 2)
        if len(celular_limpo) >= 11:
            # Exemplo: '51980189144' -> '51' + '80189144'
            celular_limpo = celular_limpo[:2] + celular_limpo[3:]

        # 3. Adiciona o código do país (55 - Brasil)
        if not celular_limpo.startswith('55'):
            celular_completo = "55" + celular_limpo
        else:
            celular_completo = celular_limpo

        # 4. === TRATAMENTO DA MENSAGEM (Com Lógica Condicional) ===

        # 4.1 Define a mensagem base com base no USUARIO APP
        if user_app == "Leonardo wons":
            # Mensagem para o Leonardo (mais pessoal)
            mensagem_base = (
                f"Olá {nome}, tudo bem? "
                f"Sou o Leonardo, especialista de aplicação da Sensorville. "
            )
        else:
            # Mensagem padrão para outros consultores
            mensagem_base = (
                f"Ola {nome}, tudo bem? "
                f"Sou o {user_app}, consultor da Sensorville. "
            )

        #texto_link = f"?text={quote(mensagem_base)}"

        # 5. Constrói a URL final
        url = f"https://wa.me/{celular_completo}"

        # 6. Retorna a URL (para ser lida diretamente pelo script de automação)
        return url

    # Aplica a função em cada linha (row)
    df['LINK WHATSAPP'] = df.apply(criar_link_whatsapp, axis=1)

    # 4. Remoção das Colunas Desnecessárias
    colunas_existentes_para_remover = [col for col in COLUNAS_PARA_REMOVER if col in df.columns]

    # 5. Limpeza e Drop de Duplicatas

    # Armazenamos a coluna de split temporariamente antes de remover outras colunas.
    # Usaremos essa série para filtrar os relatórios posteriormente.
    user_app_series = df[COLUNA_ALVO_SPLIT]

    # Removemos as colunas listadas em COLUNAS_PARA_REMOVER
    df_final = df.drop(columns=colunas_existentes_para_remover, errors='ignore')

    # --- NOVO: REMOÇÃO DE LINHAS DUPLICADAS APÓS A LIMPEZA ---
    print("Removendo linhas duplicadas...")
    linhas_antes = len(df_final)
    # Remove linhas duplicadas, mantendo a primeira ocorrência
    df_final.drop_duplicates(inplace=True)
    linhas_depois = len(df_final)
    print(f"  {linhas_antes - linhas_depois} linhas duplicadas removidas.")
    # -------------------------------------------------------------

    # Removemos a coluna USUARIO APP do DataFrame FINAL que será salvo (apenas se ela não for necessária no relatório final)
    # Se você quiser que o nome do usuário/consultor permaneça no relatório final, comente a linha abaixo.
    df_final = df_final.drop(columns=[COLUNA_ALVO_SPLIT], errors='ignore')

    # 6. Agrupamento e Salvamento

    # Agrupa o DataFrame pelos usuários únicos (usando a série original antes da remoção do df_final)
    usuarios_unicos = user_app_series.unique()

    if len(usuarios_unicos) == 0 or (len(usuarios_unicos) == 1 and str(usuarios_unicos[0]).lower() in ['nan', '']):
        print("AVISO: Nenhum usuário válido encontrado na coluna 'USUARIO APP'.")
        return

    print(f"Total de {len(usuarios_unicos)} relatórios individuais a serem gerados.")

    # Itera sobre cada usuário
    for usuario in usuarios_unicos:
        # Ignora valores nulos ou vazios
        if str(usuario).lower() in ['nan', '']:
            continue

        # Filtra o DataFrame FINAL (limpo e sem duplicatas) usando o filtro da coluna original
        # Isso garante que a filtragem do df_final corresponda aos valores do df original antes de drop_duplicates
        # Mas para que a filtragem funcione corretamente após a remoção de duplicatas,
        # a coluna COLUNA_ALVO_SPLIT PRECISA estar em df_final antes de drop_duplicates.
        # Ajustei o código para que o drop seja feito DEPOIS da filtragem.

        # O melhor é recriar o df_final ANTES de remover COLUNA_ALVO_SPLIT, fazer a filtragem, e DEPOIS removê-la na cópia filtrada.

        # Recriando df_final (temporariamente mantendo COLUNA_ALVO_SPLIT)
        df_temp = df.drop(columns=colunas_existentes_para_remover, errors='ignore').drop_duplicates(inplace=False)
        df_temp[COLUNA_ALVO_SPLIT] = df[COLUNA_ALVO_SPLIT].astype(
            str).str.strip()  # Garante que a coluna de split esteja limpa

        # Filtra o DataFrame limpo (df_temp) para obter apenas os dados deste usuário
        df_usuario = df_temp[df_temp[COLUNA_ALVO_SPLIT] == usuario].copy()

        # Remove a coluna do consultor do relatório final, pois é redundante após o split
        df_usuario = df_usuario.drop(columns=[COLUNA_ALVO_SPLIT], errors='ignore')

        # Ordena de forma decrescente pela coluna 'AVALIACAO'
        df_usuario[COLUNA_ORDENACAO] = pd.to_numeric(df_usuario[COLUNA_ORDENACAO], errors='coerce')
        df_usuario = df_usuario.sort_values(by=COLUNA_ORDENACAO, ascending=False)

        # Nome do arquivo de saída (substitui caracteres inválidos para nome de arquivo)
        nome_arquivo_saida = f"relatorio_{str(usuario).strip().replace(' ', '_').lower()}.xlsx"

        # Salva o DataFrame processado em um novo arquivo XLSX
        try:
            df_usuario.to_excel(nome_arquivo_saida, index=False)
            print(f"  ✅ Relatório salvo para '{usuario}' em '{nome_arquivo_saida}'")
        except Exception as e:
            print(f"  ❌ ERRO ao salvar o relatório para '{usuario}': {e}")
            print("Verifique se a biblioteca 'openpyxl' está instalada: pip install openpyxl")

    print("\n--- Geração de Relatórios Concluída ---")


if __name__ == "__main__":
    gerar_relatorios_usuarios()
