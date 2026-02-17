# -*- coding: utf-8 -*-
#
# Arquivo: automacao_whatsapp.py
# Descrição: Script que lê uma lista de relatórios XLSX gerados, extrai os links
# de WhatsApp e abre cada link no navegador com um intervalo de espera.

import os
import time
import keyboard
import webbrowser
import pyautogui
import pandas as pd

# --- CONFIGURAÇÕES ---
# Coluna onde o link do WhatsApp foi salvo pelo script 'relatorio_por_usuario.py'
COLUNA_LINK_WHATSAPP = "LINK WHATSAPP"
# Tempo de espera entre a abertura de um link e outro (em segundos)
TEMPO_ESPERA_ABERTURA = 5
# Tempo adicional para simular a colagem/envio (em segundos)
TEMPO_ESPERA_CTRL_V = 10
# Lista de arquivos de relatório XLSX que devem ser processados
# ATENÇÃO: Substitua esta lista pelos nomes reais dos seus arquivos gerados,
# por exemplo: ['relatorio_leonardo.xlsx', 'relatorio_gabriel.xlsx']
LISTA_ARQUIVOS_RELATORIO = [
    # Exemplo (SUBSTITUA PELOS SEUS ARQUIVOS REAIS):
    "relatorio_leonardo_wons.xlsx",
    # Adicione aqui os outros arquivos XLSX gerados pelo script anterior
]

df = pd.read_excel("relatorio_leonardo_wons.xlsx")

df = df[df['NOME'] != "Cliente"].copy()

# Se você quiser processar APENAS UM ARQUIVO, comente a lista acima e use a linha abaixo:
# ARQUIVO_UNICO = "nome_do_seu_arquivo.xlsx

def iniciar_automacao():
    """Lê os relatórios, extrai os links e inicia o loop de abertura no navegador."""

    # 1. Coleta e valida a lista de arquivos a serem processados
    arquivos_para_processar = []

    # Se uma lista de arquivos foi definida, usa ela
    if LISTA_ARQUIVOS_RELATORIO:
        for f in LISTA_ARQUIVOS_RELATORIO:
            if os.path.exists(f):
                arquivos_para_processar.append(f)
            else:
                print(f"AVISO: Arquivo '{f}' não encontrado, ignorando.")

    if not arquivos_para_processar:
        print("ERRO: Nenhuma planilha de relatório válida encontrada para processar.")
        print("Verifique se 'LISTA_ARQUIVOS_RELATORIO' está configurada corretamente.")
        return

    print(f"\n--- Iniciando Automação para {len(arquivos_para_processar)} Arquivos ---")

    todas_urls = []

    # 2. Loop para ler cada relatório e extrair as URLs
    for nome_arquivo in arquivos_para_processar:
        print(f"Lendo arquivo: {nome_arquivo}...")
        try:
            # Lendo o arquivo XLSX gerado

            if COLUNA_LINK_WHATSAPP not in df.columns:
                print(
                    f"ERRO: Coluna '{COLUNA_LINK_WHATSAPP}' não encontrada em {nome_arquivo}. Verifique o nome da coluna.")
                continue

            # Aplica a função para extrair apenas a URL da fórmula HYPERLINK do Excel
            # A lista de URLs será populada com os links extraídos
            urls_do_arquivo = df[COLUNA_LINK_WHATSAPP].astype(str).str.strip()
            # Filtra apenas as linhas que começam com 'http' (são URLs válidas)
            urls_do_arquivo = urls_do_arquivo[urls_do_arquivo.str.startswith('http')].tolist()
            todas_urls.extend(urls_do_arquivo)

            print(f"  {len(urls_do_arquivo)} URLs extraídas de {nome_arquivo}.")

        except Exception as e:
            print(f"ERRO ao ler ou processar {nome_arquivo}: {e}")

    # 3. Execução da Automação (Abre os links no navegador)

    if not todas_urls:
        print("\nNenhuma URL válida foi encontrada para iniciar a automação.")
        return

    print(f"\nTotal de {len(todas_urls)} URLs prontas para serem abertas.")
    print("--- ATENÇÃO: Prepare o seu arquivo para o Ctrl+C e Mantenha o Foco no Navegador! ---")
    print(
        f"O script abrirá cada link, esperará {TEMPO_ESPERA_ABERTURA}s, e pausará por {TEMPO_ESPERA_CTRL_V}s após a abertura.")
    time.sleep(3)  # Pausa inicial para o usuário se preparar

    for i, url in enumerate(todas_urls):
        print(f"({i + 1}/{len(todas_urls)}) Abrindo URL: {url}...")

        # Abre a URL no navegador padrão
        webbrowser.open_new_tab(url)
        # Tempo de espera para o WhatsApp Web carregar
        time.sleep(TEMPO_ESPERA_ABERTURA)
        nome_do_cliente = df.iloc[i]["NOME"].lower().capitalize()
        keyboard.write(f"Olá {nome_do_cliente}, tudo bem? "
                f"Sou o Leonardo, especialista de aplicação da Sensorville. "
                f"Estou entrando em contato para me colocar à disposição para conversarmos "
                f"sobre os produtos e aplicações que mais chamaram sua atenção. "
                f"Estou encaminhando nosso portfólio para você dar uma nova olhada.")
        time.sleep(20)
        pyautogui.press("ENTER")
        time.sleep(.5)
        pyautogui.hotkey("ctrl", "c")
        time.sleep(.3)
        pyautogui.press("ENTER")
        time.sleep(2)
        pyautogui.hotkey("alt", "F4")
        #fazer apertar ENTER, colar portifolio, e enter.

    print("\n--- Automação Concluída ---")
    print("Todos os links foram abertos. Verifique o seu navegador.")


if __name__ == "__main__":
    iniciar_automacao()
    time.sleep(1)
    print(pyautogui.position())




