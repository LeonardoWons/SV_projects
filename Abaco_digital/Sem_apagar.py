import os
import sys
import time
import pandas
import threading
import seaborn as sns
import sqlite3 as sql
from tkinter import *
from datetime import datetime
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from pyModbusTCP.client import ModbusClient


class ModbusThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.rodar = False
        self.dia_hoje = datetime.now().strftime("%d")
        self.mes_hoje = datetime.now().strftime("%m")
        self.ano_hoje = datetime.now().strftime("%Y")
        self.time = datetime.now().strftime("%H:%M:%S")

        self.lista_apertado = []
        self.valor_quando_apertado = "84"

        self.valor_quando_solto = "68"
        self.lista_solto = ["0", "1", "2", "3"]

        self.dicio_botao_label = {"0": [canvas1, circ1, total_pato1], "1": [canvas2, circ2, total_pato2],
                                  "2": [canvas3, circ3, total_pato3], "3": [canvas4, circ4, total_pato4]}
        self.tempo_botao4_pressionado = None  # Armazena o tempo de pressão do botão4

        self.total_var = {"0": 0, "1": 0,"2": 0, "3": 0}

        for tb in range(4):
            cur.execute(pegaQntPato, (tb, self.dia_hoje))
            result = cur.fetchone()[0]
            self.total_var[f"{tb}"] = result
            self.atualizar(str(tb), str(self.total_var[f"{tb}"]), self.dicio_botao_label[str(tb)], True)


    def run(self):
        self.rodar = True
        while self.rodar:
            try:
                client = ModbusClient('192.168.1.7', 502, auto_open=True, timeout=5)
                botoes = [
                    client.read_holding_registers(4000, 1),
                    client.read_holding_registers(3000, 1),
                    client.read_holding_registers(2000, 1),
                    client.read_holding_registers(1000, 1),
                ]

                if None in botoes:
                    print("Erro na leitura Modbus")
                    continue

                valores_botoes_verificar = [b[0] for b in botoes]

                for botao, valor in enumerate(valores_botoes_verificar):
                    if str(botao) in self.dicio_botao_label:
                        self.atualizar(str(botao), str(valor), self.dicio_botao_label[str(botao)], False)

            except Exception as e:
                print(f"Erro: {e}")
                erro_txt.config(text=f"*erro: {e}", fg='gray22')

            time.sleep(.01)

    def atualizar(self, botao: str, valor: str, label: list, view: bool):
        if valor == self.valor_quando_apertado and botao not in self.lista_apertado:
            self.lista_apertado.append(botao)
            self.lista_solto.remove(botao)

            cur.execute(inserir_dados, (self.dia_hoje, self.mes_hoje, self.ano_hoje,
                                        self.time, botao))  # insere botao apertado
            conexao.commit()

            self.total_var[botao] += 1
            label[0].itemconfig(label[1], fill='red')
            label[2].config(text=f"Total: {self.total_var[botao]}", bg='green2')


        elif valor == self.valor_quando_solto and botao not in self.lista_solto:
            self.lista_apertado.remove(botao)
            self.lista_solto.append(botao)

            # modificar o alerta visual para cinza
            label[0].itemconfig(label[1], fill='gray30')  # reresentação do alerta de apertado/solto
            label[2].config(bg='gray30')

        if view:
            label[2].config(text=f"Total: {self.total_var[botao]}", bg='gray30')


# Função para iniciar a thread Modbus
def start_modbus_thread():
    modbus_thread.start()
    liga_abaco.destroy()


def baixa_pdf():
    dia_hoje = datetime.now().strftime("%d")

    cur.execute(pegaQntPato, ("0", dia_hoje))  # total de patos contadas hoje
    resultado1 = cur.fetchone()
    cur.execute(pegaQntPato, ("1", dia_hoje))  # total de patos contadas hoje
    resultado2 = cur.fetchone()
    cur.execute(pegaQntPato, ("2", dia_hoje))  # total de patos contadas hoje
    resultado3 = cur.fetchone()
    cur.execute(pegaQntPato, ("3", dia_hoje))  # total de patos contadas hoje
    resultado4 = cur.fetchone()

    pdict = {'doenca': nome_pato, 'quantidade': [resultado1[0], resultado2[0], resultado3[0], resultado4[0]]}
    df = pandas.DataFrame(pdict)
    plt.figure(figsize=(12, 14))
    sns.set_theme(style="darkgrid")
    ax = sns.barplot(data=df, x='doenca', y='quantidade')
    ax.tick_params(axis='x', labelrotation=45)
    plt.savefig("Plotagem.pdf", format='pdf')


# configuração do banco de dados
nome_aquivo = 'patologias.db'
caminho_exe = ""

# verifica se é um exe ou script
if getattr(sys, 'frozen', False):
    caminho_exe = os.path.dirname(sys.executable)
elif __file__:
    caminho_exe = os.path.dirname(__file__)

config_path = os.path.join(caminho_exe, nome_aquivo)  # acha o path do db

conexao = sql.connect(config_path, check_same_thread=False)
cur = conexao.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS dados(dia VARCHAR(3),"
            "mes VARCHAR(3),ano VARCHAR(5), time VARCHAR(10), doenca VARCHAR(5))")

# 'modelo' utilizado para inserir os dados
inserir_dados = ''' INSERT INTO dados(dia, mes, ano, time, doenca) VALUES(?,?,?,?,?) '''
# 'modelo' utilizado para pegar os dados
pegaQntPato = ''' SELECT COUNT(doenca) FROM dados WHERE doenca = ? AND dia = ? '''

# Configuração da interface gráfica
tela = Tk()
w, h = tela.winfo_screenwidth(), tela.winfo_screenheight()
w *= .95
h *= .85
d1 = int((tela.winfo_screenwidth() - w) // 2)
d2 = int((tela.winfo_screenheight() - h) // 2)
tela.geometry(f"{int(w)}x{int(h)}+{d1}+{d2}")
tela.config(bg="gray10", padx=30)
tela.title("Abaco digital by Sensorville")
tela.columnconfigure(0, weight=0)
tela.columnconfigure(1, weight=0)

tela.columnconfigure(2, weight=1)

tela.columnconfigure(3, weight=0)
tela.columnconfigure(4, weight=0)
tela.rowconfigure(0, weight=1)
tela.rowconfigure(1, weight=0)
tela.rowconfigure(2, weight=0)
tela.rowconfigure(3, weight=0)
tela.rowconfigure(4, weight=0)
tela.rowconfigure(5, weight=1)

# sensorville image
img_path = os.path.join(caminho_exe, "sensor_branca.png")
img1 = Image.open(img_path).resize((int(w * .5), int(h * .1)))
logo = ImageTk.PhotoImage(img1)
img_display = Label(image=logo, borderwidth=0, highlightthickness=0, bg="gray10")
img_display.grid(row=0, column=0, columnspan=5)

# Canvas para desenhar o círculo
width_canva_circ = int(w * .07)
height_canva_circ = int(w * .07)
create_oval_1 = 1
create_oval_2 = width_canva_circ - create_oval_1

font_size_label = ("Arial", int(w * .02))
font_size_contador = ("Arial", int(w * .04))

nome_pato = ["Parcial Aerossaculite", "Total Aerossaculite", "Parcial Lesão", "Total Lesão"]

canvas1 = Canvas(tela, width=width_canva_circ, height=height_canva_circ, highlightthickness=0, bg="gray10")
circ1 = canvas1.create_oval(create_oval_1, create_oval_1, create_oval_2, create_oval_2,
                            fill='gray30')  # Círculo vermelho
canvas1.grid(column=0, row=1, padx=5, pady=5)
pato1 = Label(tela, text=f"{nome_pato[0]}", bg='gold1', font=font_size_label, borderwidth=7)
pato1.grid(column=1, row=1, padx=5, pady=5)
canvas11 = Canvas(tela, width=10, height=height_canva_circ, highlightthickness=0, bg="gray10")
line1 = canvas11.create_line(0, 45, 1000, 45, fill='white', width=5)  # linha branca style
canvas11.grid(column=2, row=1, padx=30, pady=5, sticky=NSEW)
total_pato_label1 = Label(tela, text="Total encontrado", bg='gold1', font=font_size_label, borderwidth=7)
total_pato_label1.grid(column=3, row=1, padx=5, pady=5)
total_pato1 = Label(tela, text="0", bg='gray30', fg="white", font=font_size_contador)
total_pato1.grid(column=4, row=1, padx=5, pady=5)

canvas2 = Canvas(tela, width=width_canva_circ, height=height_canva_circ, highlightthickness=0, bg="gray10")
circ2 = canvas2.create_oval(create_oval_1, create_oval_1, create_oval_2, create_oval_2,
                            fill='gray30')  # Círculo vermelho
canvas2.grid(column=0, row=2, padx=5, pady=5)
pato2 = Label(tela, text=f"{nome_pato[1]}", bg='gold1', font=font_size_label, borderwidth=7)
pato2.grid(column=1, row=2, padx=5, pady=5)
canvas22 = Canvas(tela, width=10, height=height_canva_circ, highlightthickness=0, bg="gray10")
line2 = canvas22.create_line(0, 45, 1000, 45, fill='white', width=5)  # linha branca style
canvas22.grid(column=2, row=2, padx=30, pady=5, sticky=NSEW)
total_pato_label2 = Label(tela, text="Total encontrado", bg='gold1', font=font_size_label, borderwidth=7)
total_pato_label2.grid(column=3, row=2, padx=5, pady=5)
total_pato2 = Label(tela, text="0", bg='gray30', fg="white", font=font_size_contador)
total_pato2.grid(column=4, row=2, padx=5, pady=5)

canvas3 = Canvas(tela, width=width_canva_circ, height=height_canva_circ, highlightthickness=0, bg="gray10")
circ3 = canvas3.create_oval(create_oval_1, create_oval_1, create_oval_2, create_oval_2,
                            fill='gray30')  # Círculo vermelho
canvas3.grid(column=0, row=3, padx=5, pady=5)
pato3 = Label(tela, text=f"{nome_pato[2]}", bg='gold1', font=font_size_label, borderwidth=7)
pato3.grid(column=1, row=3, padx=5, pady=5)
canvas33 = Canvas(tela, width=10, height=height_canva_circ, highlightthickness=0, bg="gray10")
line3 = canvas33.create_line(0, 45, 1000, 45, fill='white', width=5)  # linha branca style
canvas33.grid(column=2, row=3, padx=30, pady=5, sticky=NSEW)
total_pato_label3 = Label(tela, text="Total encontrado", bg='gold1', font=font_size_label, borderwidth=7)
total_pato_label3.grid(column=3, row=3, padx=5, pady=5)
total_pato3 = Label(tela, text="0", bg='gray30', fg="white", font=font_size_contador)
total_pato3.grid(column=4, row=3, padx=5, pady=5)

canvas4 = Canvas(tela, width=width_canva_circ, height=height_canva_circ, highlightthickness=0, bg="gray10")
circ4 = canvas4.create_oval(create_oval_1, create_oval_1, create_oval_2, create_oval_2,
                            fill='gray30')  # Círculo vermelho
canvas4.grid(column=0, row=4, padx=5, pady=5)
pato4 = Label(tela, text=f"{nome_pato[3]}", bg='gold1', font=font_size_label, borderwidth=7)
pato4.grid(column=1, row=4, padx=5, pady=5)
canvas44 = Canvas(tela, width=10, height=height_canva_circ, highlightthickness=0, bg="gray10")
line4 = canvas44.create_line(0, 45, 1000, 45, fill='white', width=5)  # linha branca style
canvas44.grid(column=2, row=4, padx=30, pady=5, sticky=NSEW)
total_pato_label4 = Label(tela, text="Total encontrado", bg='gold1', font=font_size_label, borderwidth=7)
total_pato_label4.grid(column=3, row=4, padx=5, pady=5)
total_pato4 = Label(tela, text="0", bg='gray30', fg="white", font=font_size_contador)
total_pato4.grid(column=4, row=4, padx=5, pady=5)

# Botão para iniciar a comunicação Modbus
erro_txt = Label(tela, text="*erro", bg='gray10', fg='gray10', font=font_size_label)
erro_txt.grid(column=0, row=5, padx=10, pady=0, columnspan=5, sticky="W")

liga_abaco = Button(tela, text="Iniciar Modbus", bg='gold1', command=start_modbus_thread)
liga_abaco.grid(column=0, row=5, columnspan=5, padx=10, pady=0)

baixar_abaco = Button(tela, text="Baixar", bg='gold1', command=baixa_pdf)
baixar_abaco.grid(column=0, row=5, columnspan=5, padx=10, pady=0, sticky="E")

# Inicializa a thread Modbus
modbus_thread = ModbusThread()

tela.mainloop()
