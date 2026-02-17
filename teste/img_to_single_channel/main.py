import cv2

# Ler a imagem colorida
img = cv2.imread("3.jpg")

# Converter para escala de cinza
img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Salvar resultado
cv2.imwrite("3.png", img_gray)
