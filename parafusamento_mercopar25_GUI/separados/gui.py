import tkinter as tk
from PIL import Image, ImageTk
import threading
import time
from modbus_com import circle_data, update_modbus_data, write_on_jaka

# ======== Cores e variáveis globais ========
sv_color = "#ecc131"
cruz_state = False
triangulo_state = False
interacao_liberada = True
modbus_thread_started = False  # só inicia o Modbus depois de clicar em "Começar"

title_text = "Setup"

# ======== Posições relativas ========
REL_CRUZ_X = 0.335
REL_TRI_X = 0.675
REL_Y = 0.37
PIECE_SIZEx = 180
PIECE_SIZEy = 135


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


def update_circle_colors(canvas, circle_items_cruz, circle_items_tri, botao):
    """Atualiza as cores dos círculos em loop."""
    global interacao_liberada, cruz_state, triangulo_state
    while True:
        try:
            for i in range(1, 5):
                color = circle_data.get(f"color_cruz_circle{i}", "gray")
                canvas.itemconfig(circle_items_cruz[f"cruz{i}"], fill=color)

            for i in range(1, 3 + 1):
                color = circle_data.get(f"color_tri_circle{i}", "gray")
                canvas.itemconfig(circle_items_tri[f"tri{i}"], fill=color)

            # Quando o Modbus indicar pronto=True, reabilita o botão
            if circle_data.get("pronto"):
                botao.config(state="normal")
                interacao_liberada = True
                title.configure("Setup")
                cruz_state = False
                triangulo_state = False
                write_on_jaka(cruz_state, triangulo_state)
                for item in circle_items_cruz.values():
                    canvas.itemconfigure(item, state="hidden")
                    canvas.tag_raise(item)
                for item in circle_items_cruz.values():
                    canvas.itemconfigure(item, state="hidden")
                    canvas.tag_raise(item)
                break

            time.sleep(0.4)

        except tk.TclError:
            break
        except Exception as e:
            print(f"[ERRO UPDATE] {e}")


def criar_tela():
    global interacao_liberada, modbus_thread_started, title
    interacao_liberada = True

    write_on_jaka(cruz_state, triangulo_state)

    root = tk.Tk()
    root.title("Setup")
    root.attributes("-fullscreen", True)
    root.overrideredirect(True)

    largura = root.winfo_screenwidth()
    altura = root.winfo_screenheight()

    canvas = tk.Canvas(root, width=largura, height=altura, highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    # ===== Imagens =====
    bg_img = Image.open("../imgs/bg.png").resize((largura, altura))
    bg_photo = ImageTk.PhotoImage(bg_img)

    cx_img = Image.open("../imgs/cx.png").convert("RGBA").resize((766, 425))
    cx_photo = ImageTk.PhotoImage(cx_img)

    cruz_img = Image.open("../imgs/cruz.png").convert("RGBA").resize((PIECE_SIZEx, PIECE_SIZEy))
    cruz_photo = ImageTk.PhotoImage(cruz_img)

    tri_img = Image.open("../imgs/triangulo.png").convert("RGBA").resize((170, 123))
    tri_photo = ImageTk.PhotoImage(tri_img)

    # ===== Fundo e caixa =====
    canvas.create_image(0, 0, image=bg_photo, anchor="nw")
    canvas.create_image(largura // 2, altura // 2 + 25, image=cx_photo, anchor="center")

    title = tk.Label(root, text="Setup", font=("Arial", 25, "bold"), fg="black", bg="white")
    canvas.create_window(int(largura * 0.27), int(altura * 0.135), window=title, anchor="center")

    # ===== Peças =====
    cruz_x, cruz_y = int(largura * REL_CRUZ_X), int(altura * REL_Y)
    tri_x, tri_y = int(largura * REL_TRI_X), int(altura * REL_Y)

    cruz_item = canvas.create_image(cruz_x, cruz_y, image=cruz_photo, anchor="center", state="hidden")
    tri_item = canvas.create_image(tri_x, tri_y, image=tri_photo, anchor="center", state="hidden")

    # ===== Círculos =====
    circle_items_cruz = {}
    circle_items_tri = {}
    radius = 12
    circle_items_cruz["cruz1"] = canvas.create_oval(
        (cruz_x + 5) - radius, (cruz_y - 52) - radius, (cruz_x + 5) + radius, (cruz_y - 52) + radius,
        fill="gray", outline="black", width=2, state="hidden"
    )
    circle_items_cruz["cruz2"] = canvas.create_oval(
        (cruz_x + 63) - radius, (cruz_y - 3) - radius, (cruz_x + 63) + radius, (cruz_y - 3) + radius,
        fill="gray", outline="black", width=2, state="hidden"
    )
    circle_items_cruz["cruz3"] = canvas.create_oval(
        (cruz_x - 2) - radius, (cruz_y + 50) - radius, (cruz_x - 2) + radius, (cruz_y + 50) + radius,
        fill="gray", outline="black", width=2, state="hidden"
    )
    circle_items_cruz["cruz4"] = canvas.create_oval(
        (cruz_x - 60) - radius, (cruz_y - 3) - radius, (cruz_x - 60) + radius, (cruz_y - 3) + radius,
        fill="gray", outline="black", width=2, state="hidden"
    )

    circle_items_tri["tri1"] = canvas.create_oval(
        (tri_x - 70) - radius, (tri_y - 45) - radius, (tri_x - 70) + radius, (tri_y - 45) + radius,
        fill="gray", outline="black", width=2, state="hidden"
    )
    circle_items_tri["tri2"] = canvas.create_oval(
        (tri_x + 48) - radius, (tri_y - 2) - radius, (tri_x + 48) + radius, (tri_y - 2) + radius,
        fill="gray", outline="black", width=2, state="hidden"
    )
    circle_items_tri["tri3"] = canvas.create_oval(
        (tri_x - 65) - radius, (tri_y + 45) - radius, (tri_x - 65) + radius, (tri_y + 45) + radius,
        fill="gray", outline="black", width=2, state="hidden"
    )

    # ===== Eventos de clique =====
    half = PIECE_SIZEx // 2
    cruz_bbox = (cruz_x - half, cruz_y - half, cruz_x + half, cruz_y + half)
    tri_bbox = (tri_x - half, tri_y - half, tri_x + half, tri_y + half)

    def on_canvas_click(event):
        if not interacao_liberada:
            return
        x, y = event.x, event.y
        if cruz_bbox[0] <= x <= cruz_bbox[2] and cruz_bbox[1] <= y <= cruz_bbox[3]:
            toggle_cruz(canvas, cruz_item)
        elif tri_bbox[0] <= x <= tri_bbox[2] and tri_bbox[1] <= y <= tri_bbox[3]:
            toggle_triangulo(canvas, tri_item)

    canvas.bind("<Button-1>", on_canvas_click)

    # ===== Botão "Começar" =====
    def start_modbus():
        global interacao_liberada, modbus_thread_started

        title.configure(text="Em parafusamento")

        interacao_liberada = False
        botao.config(state="disabled")

        write_on_jaka(cruz_state, triangulo_state)

        # === Mostra e traz os círculos para frente ===
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

    botao = tk.Button(
        root,
        text="Começar",
        font=("Arial", 15, "bold"),
        bg=sv_color,
        fg="black",
        width=12,
        command=start_modbus
    )
    canvas.create_window(largura // 2, int(altura * 0.87), window=botao, anchor="center")

    # ===== Atualização contínua =====
    threading.Thread(target=update_circle_colors, args=(canvas, circle_items_cruz, circle_items_tri, botao), daemon=True).start()

    root.bind("<Escape>", lambda e: root.destroy())
    root._images = (bg_photo, cx_photo, cruz_photo, tri_photo)
    root.mainloop()


# ========================
# Executar
# ========================
if __name__ == "__main__":
    criar_tela()
