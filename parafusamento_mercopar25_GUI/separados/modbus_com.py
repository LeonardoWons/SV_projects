# -*- coding: utf-8 -*-
import time
from pymodbus.client import ModbusTcpClient

# ===== Variável global compartilhada =====
circle_data = {
    "cruz_border": False,
    "tri_border": False,
    "screw_error": False,
    "pronto": False,

    # Estados internos
    "feito_tri_circle1": False,
    "feito_tri_circle2": False,
    "feito_tri_circle3": False,
    "feito_cruz_circle1": False,
    "feito_cruz_circle2": False,
    "feito_cruz_circle3": False,
    "feito_cruz_circle4": False,

    "erro_tri_circle1": False,
    "erro_tri_circle2": False,
    "erro_tri_circle3": False,
    "erro_cruz_circle1": False,
    "erro_cruz_circle2": False,
    "erro_cruz_circle3": False,
    "erro_cruz_circle4": False,

    # Cores iniciais
    "color_tri_circle1": "gray",
    "color_tri_circle2": "gray",
    "color_tri_circle3": "gray",
    "color_cruz_circle1": "gray",
    "color_cruz_circle2": "gray",
    "color_cruz_circle3": "gray",
    "color_cruz_circle4": "gray",
}

# ===== Configuração do cliente Modbus =====
modbus_host = '192.168.1.150'
modbus_port = 502
client = ModbusTcpClient(modbus_host, port=modbus_port)

# ===== Endereços Modbus =====
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

# ===== Função envia peças =====
def write_on_jaka(cruz_state, triangulo_state):
    client.connect()
    client.write_coil(write_modbus_registers["faz_cruz"], cruz_state)
    client.write_coil(write_modbus_registers["faz_tri"], triangulo_state)
    client.close()

# ===== Função de comunicação =====
def update_modbus_data():
    """
    Atualiza periodicamente os dados dos círculos conforme os registros Modbus.
    Essa função deve ser chamada em uma thread separada.
    """
    print("[MODBUS] Iniciando comunicação com o robô...")
    while not circle_data["pronto"]:
        try:
            if not client.connect():
                print("[MODBUS] Falha na conexão, tentando novamente...")
                time.sleep(2)
                continue

            # Ler registros Modbus
            for key, reg in read_modbus_registers.items():
                response = client.read_discrete_inputs(reg, count=1)
                if not response.isError():
                    circle_data[key] = bool(response.bits[0])

            # Atualiza status de erro geral
            screw_error = circle_data["screw_error"]
            print(circle_data)

            if circle_data["fazendo_tri"]:
                for i in range(1, 4):
                    circle_key = f"tri_circle{i}"

                    if circle_data[f"circle{i}"] and screw_error:
                        circle_data[f"erro_{circle_key}"] = True

                    if circle_data[f"circle{i}"] and not circle_data[f"erro_{circle_key}"]:
                        circle_data[f"color_{circle_key}"] = "blue"
                        circle_data[f"feito_{circle_key}"] = True

                    if circle_data[f"feito_{circle_key}"] and not circle_data[f"circle{i}"]:
                        circle_data[f"color_{circle_key}"] = "red" if circle_data[f"erro_{circle_key}"] else "green"

            elif circle_data["fazendo_cruz"]:
                for i in range(1, 5):
                    circle_key = f"cruz_circle{i}"

                    if circle_data[f"circle{i}"] and screw_error:
                        circle_data[f"erro_{circle_key}"] = True

                    if circle_data[f"circle{i}"] and not circle_data[f"erro_{circle_key}"]:
                        circle_data[f"color_{circle_key}"] = "blue"
                        circle_data[f"feito_{circle_key}"] = True

                    if circle_data[f"feito_{circle_key}"] and not circle_data[f"circle{i}"]:
                        circle_data[f"color_{circle_key}"] = "red" if circle_data[f"erro_{circle_key}"] else "green"

            time.sleep(0.3)

        except Exception as e:
            print(f"[MODBUS] Erro na leitura: {e}")
            time.sleep(1)
        finally:
            client.close()
