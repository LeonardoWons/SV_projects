# -*- coding: utf-8 -*-
import os
from flask import Flask, jsonify, render_template
import time
import threading
from pymodbus.client import ModbusTcpClient

# Variável global para armazenar os valores dos círculos e status
circle_data = {
    "cruz_border": False,
    "play_border": False,
    "VE_error": False,
    "screw_error": False,

    "feito_play_circle1": False,
    "feito_play_circle2": False,
    "feito_play_circle3": False,
    "feito_cruz_circle1": False,
    "feito_cruz_circle2": False,
    "feito_cruz_circle3": False,
    "feito_cruz_circle4": False,

    "erro_play_circle1": False,
    "erro_play_circle2": False,
    "erro_play_circle3": False,
    "erro_cruz_circle1": False,
    "erro_cruz_circle2": False,
    "erro_cruz_circle3": False,
    "erro_cruz_circle4": False,

    "color_play_circle1": "gray",
    "color_play_circle2": "gray",
    "color_play_circle3": "gray",
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
modbus_registers = {
    "cruz_circle1": 28,
    "cruz_circle2": 29,
    "cruz_circle3": 30,
    "cruz_circle4": 31,
    "play_circle1": 25,
    "play_circle3": 26,
    "play_circle2": 27,
    "achou_cruz": 9,
    "achou_play": 8,
    "VE_error": 13,
    "screw_error": 23,
    "inspect_mode": 19
}

address_erro = 98
address_last_torque = 100


# Função para atualizar os dados periodicamente
def update_modbus_data():
    while True:
        if client.connect():
            try:
                # Lê todos os registros e atualiza o dicionário
                for key, register in modbus_registers.items():
                    response = client.read_discrete_inputs(register, 1, unit=1)
                    if not response.isError():
                        circle_data[key] = bool(response.bits[0])

                # Lógica de cores para os círculos do play
                for i in range(1, 4):
                    circle_key = "play_circle{}".format(i)

                    if circle_data[circle_key] and circle_data["screw_error"]:  # identifica erro parafuso
                        circle_data["erro_{}".format(circle_key)] = True
                        value = client.read_holding_registers(address_erro, 2)
                        print(value.registers[0])
                        print(str(value.registers[0] / 10000)[:2])
                        circle_data["value_{}".format(circle_key)] = str(value.registers[0] / 10000)[:2]

                    if circle_data[circle_key] and not circle_data["erro_{}".format(circle_key)]:  # se estiver fazendo e não tiver erro
                        circle_data["color_{}".format(circle_key)] = "blue"
                        circle_data["feito_{}".format(circle_key)] = True
                        value_t = client.read_holding_registers(address_last_torque, 2)
                        print(value_t.registers[0])
                        print(str(value_t.registers[0] / 10000)[:2])
                        circle_data["value_{}".format(circle_key)] = str(value_t.registers[0] / 10000)[:2]

                    if circle_data["feito_{}".format(circle_key)] and not circle_data[circle_key]:  # se já foi feito, se tiver erro = red, else green
                        circle_data["color_{}".format(circle_key)] = "red" if circle_data["erro_{}".format(circle_key)] else "green"

                # Lógica de cores para os círculos da cruz
                for i in range(1, 5):
                    circle_key = "cruz_circle{}".format(i)

                    if circle_data[circle_key] and circle_data["screw_error"]:  # identifica erro parafuso
                        circle_data["erro_{}".format(circle_key)] = True
                        value = client.read_holding_registers(address_erro, 2)
                        print(value.registers[0])
                        print(str(value.registers[0] / 10000)[:2])
                        circle_data["value_{}".format(circle_key)] = str(value.registers[0] / 10000)[:2]

                    if circle_data[circle_key] and not circle_data["erro_{}".format(circle_key)]:  # se estiver fazendo e não tiver erro
                        circle_data["color_{}".format(circle_key)] = "blue"
                        circle_data["feito_{}".format(circle_key)] = True
                        value = client.read_holding_registers(address_erro, 2)
                        print(value.registers[0])
                        print(str(value.registers[0] / 10000)[:2])
                        circle_data["value_{}".format(circle_key)] = str(value.registers[0] / 10000)[:2]

                    if circle_data["feito_{}".format(circle_key)] and not circle_data[circle_key]:  # se já foi feito, se tiver erro = red, else green
                        circle_data["color_{}".format(circle_key)] = "red" if circle_data["erro_{}".format(circle_key)] else "green"

                if circle_data["inspect_mode"]:
                    time.sleep(3)
                    for i in range(1, 5):
                        circle_key_inspect = "cruz_circle{}".format(i)
                        circle_data["color_{}".format(circle_key_inspect)] = "gray"
                        circle_data["feito_{}".format(circle_key_inspect)] = False
                        circle_data["erro_{}".format(circle_key_inspect)] = False
                        circle_data["value_{}".format(circle_key_inspect)] = " "

                    for i in range(1, 4):
                        circle_key_inspect = "play_circle{}".format(i)
                        circle_data["color_{}".format(circle_key_inspect)] = "gray"
                        circle_data["feito_{}".format(circle_key_inspect)] = False
                        circle_data["erro_{}".format(circle_key_inspect)] = False
                        circle_data["value_{}".format(circle_key_inspect)] = " "

            except Exception as e:
                print("Erro ao ler registros Modbus: {}".format(e))
            finally:
                client.close()

        time.sleep(1)  # Intervalo de 1 segundo entre as leituras


# Caminhos absolutos para templates e arquivos estáticos
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client', 'templates')
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client', 'static')
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)


@app.route('/')
def index():
    return render_template('new.html')


@app.route('/data')
def get_data():
    return jsonify(circle_data)


if __name__ == '__main__':
    t = threading.Thread(target=update_modbus_data)
    t.daemon = True
    t.start()
    app.run(host='0.0.0.0', port=10010)
