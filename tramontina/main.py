import time
from datetime import datetime
import base64
import requests
import threading
from flask import Flask, request, jsonify
from pymodbus.client import ModbusTcpClient

# ---------------- CONFIG ----------------
# ADAM-6050
ADAM_IP = "10.16.135.21"
ADAM_PORT = 502
entradas = 0         # Entradas > endereço 00001
semaforo = 16        # Saida 0 > address 00016 semaforo
cancela_led = 17     # Saida 1 > address 00017 cancela led
camera_trigger = 18  # Saida 2 > address 00018 camera trigger
cancela_abre = 19    # Saida 3 > address 00019 Abre cancela
cancela_fecha = 20   # Saida 4 > address 00020 Fecha cancela
red_led = 21         # Saida 5 > address 00021 Fecha cancela

# API CAD710
API_URL = "http://mulinfsv0015:9000/api/v1/placas-validar-acesso"
API_USER = "Sensorville"
API_PASS = "9PKi9J2g1pPH5af"
CAMERA_ID = "10.16.135.22"
MAC = "F8-D4-62-01-A4-9A"

# Flask
app = Flask(__name__)

# Modbus
client = ModbusTcpClient(ADAM_IP, port=ADAM_PORT)
modbus_lock = threading.Lock()

# ---------------- ESTADO CENTRAL ----------------
class EstadoCancela:
    def __init__(self):
        self.lock = threading.Lock()
        self.last_post_time = None
        self.cancela_ativa = False
        self.sensor_desativado_inicio = time.time()
        self.permissao_fechar_cancela = False
        self.find_plate = False
        self.sensor_ativo = True

estado = EstadoCancela()

# ---------------- FLASK API ----------------
@app.route("/api/", methods=["POST"])
def receive_plate():

    data = request.get_json()

    # Salva imagem se vier
    imagem_base64 = data.get("img")
    if imagem_base64:
        with open(f"C:/Software/imgs/img{data.get("placa")}_{data.get("timestamp")}.jpeg", "wb") as f:
            f.write(base64.b64decode(imagem_base64))
        print(f"Imagem salva")
    plate_validation(data)
    return jsonify({"status": "ok"}), 200


def plate_validation(data):
    
    # Monta payload para API CAD710
    payload = {
        "placa": data.get("placa"),
        "data_hora": data.get("timestamp"),
        "camera_id": CAMERA_ID
    }
        
    try:
        response = requests.post(
            API_URL,
            json=payload,
            auth=(API_USER, API_PASS),
            timeout=3
        )

        if response.status_code == 200:

            resp_json = response.json()
            status = resp_json.get("status")
            print("Resposta API CAD710:", resp_json)

            if status == "Aprovado":

                with estado.lock:
                    estado.cancela_ativa = True
                    estado.last_post_time = time.time()
                    estado.find_plate = True
                write_coil_safe(red_led, False)
                write_coil_safe(cancela_led, True)
                write_coil_safe(cancela_abre, True)
                print("Cancela Aberta (Aprovado)")

            else:
                with estado.lock:
                    if estado.permissao_fechar_cancela:
                        write_coil_safe(cancela_fecha, True)
                        estado.cancela_ativa = False
                write_coil_safe(cancela_led, False)
                write_coil_safe(semaforo, False)
                blink_new_red_led(0.5, 5)

                print("Cancela fechada (Reprovado)")

        else:
            print("Erro API CAD710:", response.status_code)
            with estado.lock:
                if estado.permissao_fechar_cancela:
                    write_coil_safe(cancela_fecha, True)
                    estado.cancela_ativa = False
            blink_new_red_led(0.5, 5)
            write_coil_safe(cancela_led, False)
            write_coil_safe(semaforo, False)


    except Exception as e:
        print("Erro comunicação API CAD710:", e)
        with estado.lock:
            if estado.permissao_fechar_cancela:
                write_coil_safe(cancela_fecha, True)
                estado.cancela_ativa = False
        blink_new_red_led(0.5, 5)
        write_coil_safe(cancela_led, False)
        write_coil_safe(semaforo, False)



# ---------------- WRITE ON ADAM ----------------
def write_coil_safe(addr, value):
    """Escrita segura Modbus"""
    with modbus_lock:
        if not client.connect():
            print("Erro: não conectou ao Modbus")
            return False
        try:
            client.write_coil(addr, value)
            if addr == cancela_abre or addr == cancela_fecha:
                invrt_value = not value
                time.sleep(0.4)
                client.write_coil(addr, invrt_value)
            return True
        except Exception as e:
            print(f"Erro Modbus write_coil ({addr}):", e)
            return False
    


# ---------------- THREAD MONITOR INPUT ----------------
def monitor_inputs():
    """Monitora barreira e controla trigger da camera + Monitora tempo de acionamento do sensor de massa"""
    
    trigger_on = False
    sensor_ativo_anterior = False

    while True:
        try:
            with modbus_lock:
                rr = client.read_discrete_inputs(entradas, count=6)
        except Exception as e:
            print("Erro monitor input:", e)
            time.sleep(0.05)
            continue

        if rr.isError():
            time.sleep(0.01)
            continue

        barreira_ativa = rr.bits[3]
        sensor_ativo = rr.bits[5]

        with estado.lock:
            
            # SENSOR DE MASSA
            if sensor_ativo:
                estado.permissao_fechar_cancela = False

            # Detecta transição ATIVO → DESATIVADO
            if not sensor_ativo and sensor_ativo_anterior:
                estado.sensor_desativado_inicio = time.time()

            estado.sensor_ativo = sensor_ativo

            if barreira_ativa and estado.permissao_fechar_cancela and estado.last_post_time:
                if time.time() - estado.last_post_time >= 7:
                    write_coil_safe(cancela_fecha, True)
                    estado.cancela_ativa = False
                
        sensor_ativo_anterior = sensor_ativo

        # 1️⃣ Se barreira ativou → liga trigger
        if barreira_ativa and not trigger_on:
            print("Barreira ativa → Trigger ON")
            write_coil_safe(camera_trigger, True)
            
            trigger_on = True
            
            
        with estado.lock:
            # 2️⃣ Se placa encontrada E não há mais barreira → desliga trigger
            if trigger_on and estado.find_plate:
                print("Placa encontrada e barreira livre → Trigger OFF")
                write_coil_safe(camera_trigger, False)
                estado.find_plate = False
                trigger_on = False

        time.sleep(0.1)


# ---------------- THREAD MONITOR TIMEOUT ----------------
def blink_new_red_led(delay_s, qnt):
    for i in range(qnt):
        write_coil_safe(red_led, True)
        time.sleep(delay_s)
        write_coil_safe(red_led, False)
        time.sleep(delay_s)
    write_coil_safe(red_led, True)

# ---------------- THREAD MONITOR TIMEOUT ----------------
def monitor_timeout():

    while True:

        with estado.lock:
            last_post = estado.last_post_time
            ativa = estado.cancela_ativa
            inicio_sensor = estado.sensor_desativado_inicio
            sens_ativo = estado.sensor_ativo

        # -------- Monitor cancela_led --------
        if last_post and (time.time() - last_post >= 4):
            write_coil_safe(cancela_led, False)
            write_coil_safe(red_led, True)

        # -------- Monitor sensor de massa --------
        if inicio_sensor:
            tempo_desde_ultimo_carro = time.time() - inicio_sensor
            if tempo_desde_ultimo_carro >= 2:
                with estado.lock:
                    if not sens_ativo:
                        estado.permissao_fechar_cancela = True
                        
        # -------- Monitor cancela --------
        if ativa and last_post:
            if time.time() - last_post >= 7:
                with estado.lock:
                    if estado.permissao_fechar_cancela:
                        print("Timeout: fechamento automatico por falta de POST")
                        write_coil_safe(cancela_led, False)
                        write_coil_safe(red_led, True)
                        write_coil_safe(semaforo, True)
                        write_coil_safe(cancela_fecha, True)
                        estado.cancela_ativa = False

        time.sleep(0.1)


# ---------------- MAIN ----------------
if __name__ == "__main__":
    threading.Thread(target=monitor_inputs, daemon=True).start()
    threading.Thread(target=monitor_timeout, daemon=True).start()
    write_coil_safe(semaforo, True)
    write_coil_safe(cancela_led, False)
    write_coil_safe(red_led, True)
    with estado.lock:
        if estado.permissao_fechar_cancela:
            write_coil_safe(cancela_fecha, True)
            estado.cancela_ativa = False
    write_coil_safe(camera_trigger, False)
    
    app.run(host="10.16.135.22", port=80)
