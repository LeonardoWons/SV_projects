# -*- coding: utf-8 -*-
import time
from pymodbus.client import ModbusTcpClient

from testes.gui import cruz_state, triangulo_state

# Variável global para armazenar os valores dos círculos e status
circle_data = {
    "cruz_border": False,
    "tri_border": False,
    "screw_error": False,

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

    "color_tri_circle1": "gray",
    "color_tri_circle2": "gray",
    "color_tri_circle3": "gray",
    "color_cruz_circle1": "gray",
    "color_cruz_circle2": "gray",
    "color_cruz_circle3": "gray",
    "color_cruz_circle4": "gray",
}

# Configuração do cliente Modbus
modbus_host = '10.5.5.100'  # IP do dispositivo Modbus
modbus_port = 502           # Porta padrão do Modbus TCP
client = ModbusTcpClient(modbus_host, port=modbus_port)

# Endereços dos registros Modbus
read_modbus_registers = {
    "circle1": 8,
    "circle2": 9,
    "circle3": 10,
    "circle4": 11,
    "fazendo_tri": 12,
    "fazendo_cruz": 13,
    "pronto": 14,
    "screw_error": 15,
}

write_modbus_registers = {
    "faz_cruz": 40,
    "faz_tri": 41,
}

def write_on_jaka():
    client.connect()
    client.write_coil(write_modbus_registers["faz_cruz"], cruz_state)
    client.write_coil(write_modbus_registers["faz_tri"], triangulo_state)
    client.close()

# Função para atualizar os dados periodicamente
def update_modbus_data():
    while True:
        if client.connect():
            try:
                # Lê todos os registros e atualiza o dicionário
                for key, register in read_modbus_registers.items():
                    response = client.read_discrete_inputs(register, count=1)
                    if not response.isError():
                        circle_data[key] = bool(response.bits[0])

                if circle_data["fazendo_tri"]:
                    # Lógica de cores para os círculos do triangulo
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
                    # Lógica de cores para os círculos da cruz
                    for i in range(1, 5):
                        circle_key = "cruz_circle{}".format(i)

                        if circle_data[f"circle{i}"] and circle_data["screw_error"]:  # identifica erro parafuso
                            circle_data["erro_{}".format(circle_key)] = True

                        if circle_data[f"circle{i}"] and not circle_data["erro_{}".format(circle_key)]:  # se estiver fazendo e não tiver erro
                            circle_data["color_{}".format(circle_key)] = "blue"
                            circle_data["feito_{}".format(circle_key)] = True

                        if circle_data["feito_{}".format(circle_key)] and not circle_data[f"circle{i}"]:  # se já foi feito, se tiver erro = red, else green
                            circle_data["color_{}".format(circle_key)] = "red" if circle_data["erro_{}".format(circle_key)] else "green"
                else:
                    print("Ue")

            except Exception as e:
                print("Erro ao ler registros Modbus: {}".format(e))
            finally:
                client.close()

        time.sleep(1)  # Intervalo de 1 segundo entre as leituras

write_on_jaka()