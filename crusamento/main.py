from pyModbusTCP.client import ModbusClient

import pygame
import time

# Inicialização do Pygame
pygame.init()

# Definições de cores
BLACK = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)

# Configurações da janela
WIDTH, HEIGHT = 800, 700
WINDOW_SIZE = (WIDTH, HEIGHT)
screen = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption("Jogo do Cruzamento")

# Variável para controlar a luz
luz_ativa = 1
last_time_luz_ativa_changed = time.time()

# Conect to client
c = ModbusClient("192.168.1.7", port=502, debug=False, auto_open=True)

#

# Função para desenhar o cruzamento
def draw_cruzamento():
    screen.fill(WHITE)
    pygame.draw.rect(screen, BLACK, pygame.Rect(-10, -10, WIDTH / 3, HEIGHT / 3), 5)
    pygame.draw.rect(screen, BLACK, pygame.Rect((2 * WIDTH / 3) + 10, - 10, WIDTH / 3, HEIGHT / 3), 5)
    pygame.draw.rect(screen, BLACK, pygame.Rect(-10, (2 * HEIGHT / 3) + 10, WIDTH / 3, HEIGHT / 3), 5)
    pygame.draw.rect(screen, BLACK, pygame.Rect((2 * WIDTH / 3) + 10, (2 * HEIGHT / 3) + 10, WIDTH / 3, HEIGHT / 3), 5)


def draw_luz(cor):
    # Desenhar a luz
    pygame.draw.circle(screen, cor, (WIDTH / 2, HEIGHT / 2), 20)

# Loop principal do jogo
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    a = c.read_holding_registers(1001, 1)
    b = c.read_holding_registers(2001, 1)
    time.sleep(.1)

    # Desenhar o cruzamento
    draw_cruzamento()

    # Verificar se a luz deve mudar
    if int(a[0]) == 256 or int(b[0]) == 256:
        draw_luz(RED)

    elif int(a[0]) == 0 and int(b[0]) == 0:
        draw_luz(BLACK)

    # Atualizar a tela
    pygame.display.flip()

    # Delay para manter uma taxa de quadros constante
    pygame.time.delay(10)

# Finalização do Pygame
pygame.quit()
