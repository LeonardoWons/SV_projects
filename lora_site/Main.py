import paho.mqtt.client as mqtt
import json
from datetime import datetime

# Configurações do MQTT
BROKER = "192.168.1.1"
PORT = 1883
TOPIC = "#"
USERNAME = "admin"
PASSWORD = "admin"

# Callback ao conectar
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Conectado com sucesso ao MQTT Broker!")
        client.subscribe(TOPIC)
        print(f"📡 Inscrito no tópico: {TOPIC}")
    else:
        print(f"❌ Falha na conexão. Código: {rc}")

# Callback ao receber mensagens
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)

        print("-" * 60)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Pacote recebido")
        print(f"Device: {data.get('name')}")
        print(f"RSSI: {data.get('rssi')} dBm")
        print(f"SNR (lsnr): {data.get('lsnr')}")
        print(f"Pacotes perdidos: {data.get('packet_loss')}")
        print(f"Payload bruto: {data.get('data')}")
        print(f"Contador (fcnt): {data.get('fcnt')}")
        print(f"Frequência LoRa: {data.get('freq')} MHz")

    except Exception as e:
        print("⚠️ Erro ao processar mensagem:", e)

# Cria o cliente MQTT
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

print("🔍 Site Survey iniciado — aguardando conexão com o broker...")
client.connect(BROKER, PORT, 60)
client.loop_forever()
