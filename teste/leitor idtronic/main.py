import socket
from time import sleep


def calcular_bcc(packet_bytes):
    bcc = 0
    for b in packet_bytes:
        bcc ^= b
    return bcc

def montar_pacote_tcp(cmd, dados=None):
    if dados is None:
        dados = []

    STX = 0xAA
    ETX = 0xBB
    station_id = 0x00
    data_length = 1 + len(dados)
    corpo = [station_id, data_length, cmd] + dados
    bcc = calcular_bcc(corpo)
    return bytes([STX] + corpo + [bcc, ETX])

def ler_uid_cartao(ip, porta):
    with socket.create_connection((ip, porta), timeout=2) as s:
        comando = montar_pacote_tcp(0x25, [0x26, 0x00])
        s.sendall(comando)
        resposta = s.recv(32)
        print("Resposta recebida:", resposta.hex())

        if resposta[0] == 0xAA and resposta[-1] == 0xBB and resposta[3] == 0x00:
            snr_bytes = resposta[5:-2]  # UID do cartão
            snr_hex = ''.join(f'{b:02X}' for b in snr_bytes)
            print("UID do cartão:", snr_hex)
        else:
            print("Falha ou resposta inválida.")


def acionar_led_verde(ip, porta):
    with socket.create_connection((ip, porta), timeout=2) as s:
        # Ex: acender LED por 480ms em 2 ciclos
        comando = montar_pacote_tcp(0x88, [24, 2])  # 24*20ms = 480ms, 2 ciclos
        s.sendall(comando)
        resposta = s.recv(10)
        print("Resposta LED:", resposta.hex())


def acionar_buzzer(ip, porta, tempo_em_ms=20, ciclos=1):
    try:
        with socket.create_connection((ip, porta), timeout=2) as s:
            comando = montar_pacote_tcp(0x89, [tempo_em_ms, ciclos])
            s.sendall(comando)
            resposta = s.recv(10)
            print("Resposta do buzzer:", resposta.hex())
    except Exception as e:
        print("Erro ao acionar buzzer:", e)

while True:
    try:
        sleep(4)
        # EXEMPLO DE USO
        #ler_uid_cartao("192.168.0.104", 8000)
        #sleep(2)
        # EXEMPLO DE USO
        #acionar_led_verde("192.168.0.105", 8000)
        #sleep(2)
        # EXEMPLO DE USO
        acionar_buzzer("192.168.0.104", 8000)
        #sleep(2)
    except:
        pass
    finally:
        pass
