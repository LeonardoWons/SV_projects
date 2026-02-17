import tkinter as tk
from PIL import Image, ImageTk

# ======== Cores e variáveis globais ========
sv_color = "#ecc131"
cruz_state = False
triangulo_state = False
interacao_liberada = True  # controla se os cliques ainda são válidos

# ======== Posições relativas ========
REL_CRUZ_X = 0.29
REL_TRI_X = 0.71
REL_Y = 0.47
PIECE_SIZE = 250


def toggle_cruz(canvas, cruz_item):
    """Mostra ou esconde a cruz."""
    global cruz_state, interacao_liberada
    if not interacao_liberada:
        return  # bloqueia interação após clicar em "Começar"

    cruz_state = not cruz_state
    state = "normal" if cruz_state else "hidden"
    canvas.itemconfigure(cruz_item, state=state)
    if cruz_state:
        canvas.tag_raise(cruz_item)


def toggle_triangulo(canvas, tri_item):
    """Mostra ou esconde o triângulo."""
    global triangulo_state, interacao_liberada
    if not interacao_liberada:
        return  # bloqueia interação após clicar em "Começar"

    triangulo_state = not triangulo_state
    state = "normal" if triangulo_state else "hidden"
    canvas.itemconfigure(tri_item, state=state)
    if triangulo_state:
        canvas.tag_raise(tri_item)


def criar_tela():
    """Cria a tela inicial com as peças."""
    global interacao_liberada
    interacao_liberada = True  # reativa interações no início

    root = tk.Tk()
    root.title("Tela Inicial")
    root.attributes("-fullscreen", True)
    root.overrideredirect(True)

    largura = root.winfo_screenwidth()
    altura = root.winfo_screenheight()

    # ===== Canvas principal =====
    canvas = tk.Canvas(root, width=largura, height=altura, highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    # ====== Carregar imagens ======
    bg_img = Image.open("../imgs/bg.png").resize((largura, altura))
    bg_photo = ImageTk.PhotoImage(bg_img)

    cx_img = Image.open("../imgs/cx.png")
    cx_photo = ImageTk.PhotoImage(cx_img)

    cruz_pil = Image.open("../imgs/cruz.png").convert("RGBA").resize((PIECE_SIZE, PIECE_SIZE))
    cruz_photo = ImageTk.PhotoImage(cruz_pil)

    tri_pil = Image.open("../imgs/triangulo.png").convert("RGBA").resize((PIECE_SIZE, PIECE_SIZE))
    tri_photo = ImageTk.PhotoImage(tri_pil)

    # ====== Desenhar no Canvas ======
    canvas.create_image(0, 0, image=bg_photo, anchor="nw")
    canvas.create_image(largura // 2, altura // 2, image=cx_photo, anchor="center")

    # ===== Texto "Setup" =====
    title_label = tk.Label(
        root,
        text="Setup",
        font=("Arial", 25, "bold"),
        fg="black",
        bg="white",  # pode remover ou ajustar conforme o bg.png
    )
    canvas.create_window(int(largura * 0.27) , int(altura * 0.135), window=title_label, anchor="center")

    # ===== Coordenadas das peças =====
    cruz_x = int(largura * REL_CRUZ_X)
    cruz_y = int(altura * REL_Y)
    tri_x = int(largura * REL_TRI_X)
    tri_y = int(altura * REL_Y)

    # ===== Imagens das peças =====
    cruz_item = canvas.create_image(cruz_x, cruz_y, image=cruz_photo, anchor="center", state="hidden")
    tri_item = canvas.create_image(tri_x, tri_y, image=tri_photo, anchor="center", state="hidden")

    # ===== Hitboxes (coordenadas clicáveis) =====
    half = PIECE_SIZE // 2
    cruz_bbox = (cruz_x - half, cruz_y - half, cruz_x + half, cruz_y + half)
    tri_bbox = (tri_x - half, tri_y - half, tri_x + half, tri_y + half)

    def on_canvas_click(event):
        if not interacao_liberada:
            return  # se já começou, não faz nada
        x, y = event.x, event.y
        if cruz_bbox[0] <= x <= cruz_bbox[2] and cruz_bbox[1] <= y <= cruz_bbox[3]:
            toggle_cruz(canvas, cruz_item)
        elif tri_bbox[0] <= x <= tri_bbox[2] and tri_bbox[1] <= y <= tri_bbox[3]:
            toggle_triangulo(canvas, tri_item)

    canvas.bind("<Button-1>", on_canvas_click)

    # ===== Botão "Começar" =====
    def start_screwing():
        global interacao_liberada
        interacao_liberada = not interacao_liberada  # bloqueia os botões
        # Aqui você pode colocar a lógica do "início" real
        print("Começou!")  # exemplo visual no console

    botao = tk.Button(
        root,
        text="Começar",
        font=("Arial", 15, "bold"),
        bg=sv_color,
        fg="black",
        width=12,
        command=start_screwing
    )
    canvas.create_window(largura // 2, int(altura * 0.87), window=botao, anchor="center")

    root.bind("<Escape>", lambda e: root.destroy())

    # ===== Evita garbage collection =====
    root._images = (bg_photo, cx_photo, cruz_photo, tri_photo)
    root.mainloop()


# ========================
# Executar
# ========================
if __name__ == "__main__":
    criar_tela()
