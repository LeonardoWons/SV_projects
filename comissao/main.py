import os
import time
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configurações iniciais
usuario = "Leonardo Wons"
senha = "lokiju159"

orcamentos = []
orcamentos_processados = []
today = datetime.datetime.today().strftime('%d-%m-%Y')  # Usado para o nome do arquivo

# Configuração do WebDriver
options = webdriver.ChromeOptions()
#options.add_argument("--headless")  # Ative se quiser rodar em segundo plano
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
driver.maximize_window()

# URL do site
url = "https://sensorville.wtti.app/Login.aspx"
driver.get(url)
time.sleep(15)

# Preencher campos de login
driver.find_element(By.ID, "txtUsuario").send_keys(usuario)
driver.find_element(By.ID, "txtSenha").send_keys(senha)
driver.find_element(By.ID, "btnAcessar").click()
time.sleep(5)

# Acessa página de orçamentos
driver.get("https://sensorville.wtti.app/View/Cadastro/FilaPreOrcamento.aspx")
time.sleep(5)

# Seleciona solicitante
try:
    select_element = Select(driver.find_element(By.ID, "ddlSolicitante"))
    select_element.select_by_value("Leonardo Wons")
    time.sleep(2)
except Exception as e:
    print("Erro ao selecionar o solicitante:", e)

# Clica em pesquisar
driver.find_element(By.ID, "btnPesquisar").click()
time.sleep(5)

# Extrai os orçamentos da tabela
tabela = driver.find_element(By.CSS_SELECTOR, "table.grade.table.backgroundTable")
linhas = tabela.find_elements(By.TAG_NAME, "tr")
for linha in linhas:
    colunas = linha.find_elements(By.TAG_NAME, "td")
    if len(colunas) >= 4:
        quarta_coluna = colunas[3].text.strip()
        if quarta_coluna:
            print(type(quarta_coluna))
            print(quarta_coluna)
            if int(quarta_coluna) > 28000:
                orcamentos.append(quarta_coluna)


# Acessa página de controle de notas
driver.get("https://sensorville.wtti.app/View/Cadastro/ControleNotas.aspx")
time.sleep(5)

# Seleciona o tipo de nota
try:
    select_element = Select(driver.find_element(By.ID, "ddlTipo"))
    select_element.select_by_value("17")  # Orçamento Processado
    time.sleep(2)
except Exception as e:
    print("Erro ao selecionar o tipo de nota:", e)

"""time.sleep(1)
# ======= Preencher datas =======
hoje = datetime.date.today()
mes_atual = hoje.month - 1
ano_atual = hoje.year

mes_seguinte = mes_atual + 1
ano_final = ano_atual
if mes_seguinte == 13:
    mes_seguinte = 1
    ano_final += 1

data_inicial = f"01{mes_atual:02d}{ano_atual}"
data_final = f"01{mes_seguinte:02d}{ano_final}"

campo_data_i = driver.find_element(By.ID, "txtDataI")
campo_data_i.click()
time.sleep(1)
campo_data_i.send_keys(Keys.BACKSPACE * 20)
time.sleep(1)
campo_data_i.send_keys(data_inicial)

campo_data_f = driver.find_element(By.ID, "txtDataF")
campo_data_f.click()
time.sleep(1)
campo_data_f.send_keys(Keys.BACKSPACE * 20)
time.sleep(1)
campo_data_f.send_keys(data_final)"""

# ======= Processa os orçamentos =======
print(orcamentos)
for orc in orcamentos:
    print(orc + "\n")
    print(orcamentos_processados)
    try:
        time.sleep(3)
        input_nota = driver.find_element(By.ID, "txtNota")
        input_nota.clear()
        time.sleep(3)
        input_nota.send_keys(orc)
        time.sleep(3)
        driver.find_element(By.ID, "btnPesquisarNota").click()
        time.sleep(3)

        tabelas = driver.find_elements(By.ID, "gdwImprimeNotas")
        if len(tabelas) > 0:
            orcamentos_processados.append(orc)

    except Exception as e:
        print(f"Erro ao processar orçamento {orc}:", e)

# ======= Salvar resultados em TXT =======
arquivo_txt = f"orcamentos_processados.txt"

# Carrega orçamentos já registrados (se o arquivo existir)
orcamentos_anteriores = set()
if os.path.exists(arquivo_txt):
    with open(arquivo_txt, "r", encoding="utf-8") as f:
        orcamentos_anteriores = set(line.strip() for line in f.readlines())

# Filtra os orçamentos novos
novos_orcamentos = [orc for orc in orcamentos_processados if orc not in orcamentos_anteriores]

# Salva apenas os novos, em modo de append
with open(arquivo_txt, "a", encoding="utf-8") as f:
    for orc in novos_orcamentos:
        f.write(orc + "\n")

# Encerra login
time.sleep(10)
driver.get("https://sensorville.wtti.app/Logout.aspx")
time.sleep(5)
# Fechar o navegador ao fim
driver.quit()
