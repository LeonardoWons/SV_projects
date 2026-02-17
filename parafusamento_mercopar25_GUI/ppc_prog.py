# -*- coding: utf-8 -*-
import tkinter as tk

from PIL import Image, ImageTk
import threading
import time
from pymodbus.client import ModbusTcpClient

# ======== CONFIGURAÇÃO MODBUS ========
modbus_host = '192.168.1.150'
modbus_port = 502
client = ModbusTcpClient(modbus_host, port=modbus_port)

# ======== REGISTRADORES ========
read_modbus_registers = {
    "circle1": 8,
    "circle2": 9,
    "circle3": 10,
    "circle4": 11,
    "fazendo_tri": 13,
    "fazendo_cruz": 12,
    "pronto": 14,
    "screw_error": 15,
}
write_modbus_registers = {
    "faz_cruz": 40,
    "faz_tri": 41,
}

# ======== DADOS GLOBAIS ========
circle_data = {
    "pronto": False,
    "screw_error": False,
    "fazendo_cruz": False,
    "fazendo_tri": False,
    "title_text": "Setup",
    **{f"erro_cruz_circle{i}": False for i in range(1, 5)},
    **{f"erro_tri_circle{i}": False for i in range(1, 4)},
    **{f"feito_cruz_circle{i}": False for i in range(1, 5)},
    **{f"feito_tri_circle{i}": False for i in range(1, 4)},
    **{f"color_cruz_circle{i}": "gray" for i in range(1, 5)},
    **{f"color_tri_circle{i}": "gray" for i in range(1, 4)},
}

# ======== VARIÁVEIS GLOBAIS ========
sv_color = "#ecc131"
cruz_state = False
triangulo_state = False
interacao_liberada = True
modbus_thread_started = False


# ===========================
# FUNÇÕES DE COMUNICAÇÃO
# ===========================
def write_on_jaka(cruz_state, triangulo_state):
    """Envia ao robô quais peças estão ativas"""
    client.connect()
    client.write_coil(write_modbus_registers["faz_cruz"], cruz_state)
    client.write_coil(write_modbus_registers["faz_tri"], triangulo_state)
    client.close()


def update_modbus_data():
    """Thread que lê dados do robô periodicamente"""
    global circle_data
    while True:
        print(circle_data)
        try:
            if not client.connect():
                print("[MODBUS] Falha na conexão, tentando novamente...")
                time.sleep(2)
                continue

            # Leitura dos registros
            for key, reg in read_modbus_registers.items():
                response = client.read_discrete_inputs(reg, count=1)
                if not response.isError():
                    circle_data[key] = bool(response.bits[0])

            screw_error = circle_data["screw_error"]

            # Atualiza as cores conforme o estado atual
            if circle_data["fazendo_tri"]:
                circle_data["title_text"] = "Parafusando Triangulo"
                for i in range(1, 4):
                    circle_key = "tri_circle{}".format(i)

                    if circle_data[f"circle{i}"] and circle_data["screw_error"]:  # identifica erro parafuso
                        circle_data["erro_{}".format(circle_key)] = True

                    if circle_data[f"circle{i}"] and not circle_data["erro_{}".format(circle_key)]:  # se estiver fazendo e não tiver erro
                        circle_data["color_{}".format(circle_key)] = "blue"
                        circle_data["feito_{}".format(circle_key)] = True

                    if circle_data["feito_{}".format(circle_key)] and not circle_data[f"circle{i}"]:  # se já foi feito, se tiver erro = red, else green
                        circle_data["color_{}".format(circle_key)] = "red" if circle_data["erro_{}".format(circle_key)] else "green"

            elif circle_data["fazendo_cruz"]:
                circle_data["title_text"] = "Parafusando Cruz"
                for i in range(1, 5):
                    circle_key = "cruz_circle{}".format(i)

                    if circle_data[f"circle{i}"] and circle_data["screw_error"]:  # identifica erro parafuso
                        circle_data["erro_{}".format(circle_key)] = True

                    if circle_data[f"circle{i}"] and not circle_data["erro_{}".format(circle_key)]:  # se estiver fazendo e não tiver erro
                        circle_data["color_{}".format(circle_key)] = "blue"
                        circle_data["feito_{}".format(circle_key)] = True

                    if circle_data["feito_{}".format(circle_key)] and not circle_data[f"circle{i}"]:  # se já foi feito, se tiver erro = red, else green
                        circle_data["color_{}".format(circle_key)] = "red" if circle_data["erro_{}".format(circle_key)] else "green"

            time.sleep(0.3)

        except Exception as e:
            print(f"[MODBUS] Erro na leitura: {e}")
            time.sleep(1)
        finally:
            client.close()


# ===========================
# FUNÇÕES DE INTERFACE
# ===========================
def toggle_cruz(canvas, cruz_item):
    global cruz_state, interacao_liberada
    if not interacao_liberada:
        return
    cruz_state = not cruz_state
    state = "normal" if cruz_state else "hidden"
    canvas.itemconfigure(cruz_item, state=state)
    if cruz_state:
        canvas.tag_raise(cruz_item)


def toggle_triangulo(canvas, tri_item):
    global triangulo_state, interacao_liberada
    if not interacao_liberada:
        return
    triangulo_state = not triangulo_state
    state = "normal" if triangulo_state else "hidden"
    canvas.itemconfigure(tri_item, state=state)
    if triangulo_state:
        canvas.tag_raise(tri_item)


def update_circle_colors(canvas, circle_items_cruz, circle_items_tri, botao, title):
    """Atualiza cores e faz reset quando pronto=True"""
    global interacao_liberada, cruz_state, triangulo_state
    while True:
        try:
            title.configure(text=circle_data.get("title_text"))
            for i in range(1, 5):
                canvas.itemconfig(circle_items_cruz[f"cruz{i}"], fill=circle_data.get(f"color_cruz_circle{i}", "gray"))
            for i in range(1, 4):
                canvas.itemconfig(circle_items_tri[f"tri{i}"], fill=circle_data.get(f"color_tri_circle{i}", "gray"))

            # RESET automático
            if circle_data.get("pronto"):
                write_on_jaka(False, False)
                print("[INTERFACE] Processo concluído, resetando tela...")
                title.configure(text="Parafusamento Finalizado", fg="black")
                time.sleep(1.5)
                title.configure(text="Reiniciando sistema")
                botao.config(state="normal")
                interacao_liberada = True

                cruz_state = False
                triangulo_state = False

                for i in range(1,5):
                    circle_data[f"color_cruz_circle{i}"] = "gray"
                    circle_data[f"feito_cruz_circle{i}"] = False

                for i in range(1,4):
                    circle_data[f"color_tri_circle{i}"] = "gray"
                    circle_data[f"feito_tri_circle{i}"] = False

                # Esconde círculos
                for items in (circle_items_cruz, circle_items_tri):
                    for item in items.values():
                        canvas.itemconfigure(item, state="hidden", fill="gray")
                        time.sleep(.5)

                # Esconde peças
                canvas.itemconfigure("cruz", state="hidden")
                canvas.itemconfigure("triangulo", state="hidden")

                circle_data["pronto"] = False  # limpa flag
                print("[INTERFACE] Reset concluído.")
                time.sleep(0.5)
                circle_data["title_text"] = "Setup"
                title.configure(text="Setup", fg="black")

            time.sleep(0.3)

        except tk.TclError:
            break
        except Exception as e:
            print(f"[ERRO UPDATE] {e}")


# ===========================
# CRIAÇÃO DA INTERFACE
# ===========================
def criar_tela():
    global interacao_liberada, modbus_thread_started

    write_on_jaka(False, False)

    root = tk.Tk()
    root.title("Celula Parafusamento")
    root.attributes("-fullscreen", False)
    root.overrideredirect(False)

    largura, altura = root.winfo_screenwidth(), root.winfo_screenheight()

    canvas = tk.Canvas(root, width=largura, height=altura, highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    # ===== Imagens =====
    bg_img = Image.open("imgs/bg.png").resize((largura, altura))
    bg_photo = ImageTk.PhotoImage(bg_img)
    cx_img = Image.open("imgs/cx.png").convert("RGBA").resize((766, 425))
    cx_photo = ImageTk.PhotoImage(cx_img)
    cruz_img = Image.open("imgs/cruz.png").convert("RGBA").resize((180, 135))
    cruz_photo = ImageTk.PhotoImage(cruz_img)
    tri_img = Image.open("imgs/triangulo.png").convert("RGBA").resize((170, 123))
    tri_photo = ImageTk.PhotoImage(tri_img)

    canvas.create_image(0, 0, image=bg_photo, anchor="nw")
    canvas.create_image(largura // 2, altura // 2 + 25, image=cx_photo, anchor="center")

    title = tk.Label(root, text="Setup", font=("Arial", 25, "bold"), fg="black", bg="white")
    canvas.create_window(int(largura * 0.27), int(altura * 0.135), window=title, anchor="center")

    # ===== Peças =====
    cruz_x, cruz_y = int(largura * 0.335), int(altura * 0.37)
    tri_x, tri_y = int(largura * 0.675), int(altura * 0.37)
    cruz_item = canvas.create_image(cruz_x, cruz_y, image=cruz_photo, anchor="center", state="hidden", tags="cruz")
    tri_item = canvas.create_image(tri_x, tri_y, image=tri_photo, anchor="center", state="hidden", tags="triangulo")

    # ===== Círculos =====
    circle_items_cruz = {
        "cruz4": canvas.create_oval(cruz_x + 5 - 12, cruz_y - 52 - 12, cruz_x + 5 + 12, cruz_y - 52 + 12, fill="gray", outline="black", width=2, state="hidden"),
        "cruz2": canvas.create_oval(cruz_x + 63 - 12, cruz_y - 3 - 12, cruz_x + 63 + 12, cruz_y - 3 + 12, fill="gray", outline="black", width=2, state="hidden"),
        "cruz3": canvas.create_oval(cruz_x - 2 - 12, cruz_y + 50 - 12, cruz_x - 2 + 12, cruz_y + 50 + 12, fill="gray", outline="black", width=2, state="hidden"),
        "cruz1": canvas.create_oval(cruz_x - 60 - 12, cruz_y - 3 - 12, cruz_x - 60 + 12, cruz_y - 3 + 12, fill="gray", outline="black", width=2, state="hidden")
    }
    circle_items_tri = {
        "tri2": canvas.create_oval(tri_x - 70 - 12, tri_y - 45 - 12, tri_x - 70 + 12, tri_y - 45 + 12, fill="gray", outline="black", width=2, state="hidden"),
        "tri3": canvas.create_oval(tri_x + 48 - 12, tri_y - 2 - 12, tri_x + 48 + 12, tri_y - 2 + 12, fill="gray", outline="black", width=2, state="hidden"),
        "tri1": canvas.create_oval(tri_x - 65 - 12, tri_y + 45 - 12, tri_x - 65 + 12, tri_y + 45 + 12, fill="gray", outline="black", width=2, state="hidden")
    }

    # ===== Eventos =====
    def on_canvas_click(event):
        if not interacao_liberada:
            return
        x, y = event.x, event.y
        if abs(x - cruz_x) < 100 and abs(y - cruz_y) < 80:
            toggle_cruz(canvas, cruz_item)
        elif abs(x - tri_x) < 100 and abs(y - tri_y) < 80:
            toggle_triangulo(canvas, tri_item)

    canvas.bind("<Button-1>", on_canvas_click)

    # ===== Botão =====
    def start_modbus():
        global interacao_liberada, modbus_thread_started

        if cruz_state or triangulo_state:
            circle_data["title_text"] = "Posicionamento"
            title.configure(text="Posicionamento", fg="black")
            interacao_liberada = False
            botao.config(state="disabled")

            write_on_jaka(cruz_state, triangulo_state)

            # Mostra círculos correspondentes
            if cruz_state:
                for item in circle_items_cruz.values():
                    canvas.itemconfigure(item, state="normal")
                    canvas.tag_raise(item)
            if triangulo_state:
                for item in circle_items_tri.values():
                    canvas.itemconfigure(item, state="normal")
                    canvas.tag_raise(item)

            if not modbus_thread_started:
                threading.Thread(target=update_modbus_data, daemon=True).start()
                modbus_thread_started = True


            print("[INTERFACE] Comunicação iniciada com o robô...")
        else:
            circle_data["title_text"] = "Selecione a peça"
            title.configure(text="Selecione a peça", fg="red")

    botao = tk.Button(root, text="Começar", font=("Arial", 15, "bold"), bg=sv_color, fg="black", width=12, command=start_modbus)
    canvas.create_window(largura // 2, int(altura * 0.87), window=botao, anchor="center")

    threading.Thread(target=update_circle_colors, args=(canvas, circle_items_cruz, circle_items_tri, botao, title), daemon=True).start()

    root.bind("<Escape>", lambda e: root.destroy())
    root._images = (bg_photo, cx_photo, cruz_photo, tri_photo)
    root.mainloop()


# ===========================
# EXECUTAR
# ===========================
if __name__ == "__main__":
    criar_tela()
