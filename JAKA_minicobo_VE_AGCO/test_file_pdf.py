import fitz
from PIL import Image


def gerar_pdf_com_imagens_e_texto(img_path, textos):
    doc = fitz.open("PDF_model.pdf")
    page = doc[0]

    posicoes = [(30, 155), (312, 155), (30, 475), (312, 475)]  # Alterei Y da linha 2 para não sobrepor textos

    largura_max = 250  # em pontos (ex: 200 pts ~7cm)

    for i in range(len(img_path)):
        x, y = posicoes[i % len(posicoes)]

        # Abrir imagem com PIL para obter tamanho
        img = Image.open(img_path[i])
        largura_original, altura_original = img.size

        # Reduz proporcionalmente para a largura máxima
        if largura_original > largura_max:
            escala = largura_max / largura_original
            nova_largura = largura_original * escala
            nova_altura = altura_original * escala
        else:
            nova_largura = largura_original
            nova_altura = altura_original

        rect = fitz.Rect(x, y, x + nova_largura, y + nova_altura)
        page.insert_image(rect, filename=img_path[i])

        # Inserir os textos abaixo da imagem
        for t in range(4):
            texto_y = y + nova_altura + 21 * (t + 1)
            page.insert_text((x, texto_y), textos[i][t], fontsize=17, fontname="helv", color=(0, 0, 0))

    doc.save("static/teste.pdf")

inspecoes = ['Parafuso_1', 'Parafuso_2', 'Parafuso_3', 'Parafuso_4']
imgs_paths = [f"static/{i}.jpeg" for i in inspecoes]
textos_img = [['Data:', 'Resultado:', f'Inspeção: {insp}', 'Modelo: SV MADE'] for insp in inspecoes]

gerar_pdf_com_imagens_e_texto(imgs_paths, textos_img)