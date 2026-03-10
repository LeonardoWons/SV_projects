# Importações necessárias para o funcionamento do aplicativo
import time
from random import randint
from datetime import datetime, timezone
from flask import Flask, render_template, send_from_directory, jsonify, request, send_file
from pyModbusTCP.client import ModbusClient
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_socketio import SocketIO
from io import BytesIO
import pandas as pd

import customtkinter
import webbrowser

import threading
import os

# Inicialização do aplicativo Flask
app = Flask(__name__)

# Configuração do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sensores.db'
db = SQLAlchemy(app)

# Inicialização do SocketIO para comunicação em tempo real
socketio = SocketIO(app, cors_allowed_origins="*")

timestamp = datetime.now(timezone.utc)

treinamento_qm30_ativo = False
qm30_remain_treinamento = 0

modbus_lock = threading.Lock()

# Definição do modelo de dados para armazenar as leituras dos sensores
class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(timezone=True),server_default=func.now(), default=db.func.current_timestamp())
    value_q4x = db.Column(db.Integer)  # Valor do sensor Q4X

    qm30_hf_a_x = db.Column(db.Integer)  # Aceleração X do sensor QM30
    qm30_hf_a_y = db.Column(db.Integer)  # Aceleração Y do sensor QM30
    qm30_hf_a_z = db.Column(db.Integer)  # Aceleração Z do sensor QM30

    qm30_v_mm_x = db.Column(db.Integer)  # Velocidade X do sensor QM30
    qm30_v_mm_y = db.Column(db.Integer)  # Velocidade Y do sensor QM30
    qm30_v_mm_z = db.Column(db.Integer)  # Velocidade Z do sensor QM30

    value_qm30_temp = db.Column(db.Integer)  # Temperatura do sensor QM30

    value_b22_status = db.Column(db.Integer)  # Status do sensor B22
    value_b22_peca = db.Column(db.Integer)  # Contagem de peças do sensor B22

    value_temp = db.Column(db.Integer)  # Temperatura ambiente
    value_humid = db.Column(db.Integer)  # Umidade ambiente

    s15cct_value = db.Column(db.Integer)

    s24ASD_humidity = db.Column(db.Integer)  # Humidade ambiente
    s24ASD_temperature = db.Column(db.Integer)  # Temperatura ambiente
    s24ASD_dewpoint = db.Column(db.Integer)  # DewPoint ambiente

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    timestamp = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now()
    )

    origem = db.Column(db.String(20))   # cnc | estufa | tanque
    parametro = db.Column(db.String(50))
    valor = db.Column(db.Float)

    limite_min = db.Column(db.Float)
    limite_max = db.Column(db.Float)

    lido = db.Column(db.Boolean, default=False)

LIMITES = {
    "cnc": {
        "qm30_v_mm_x": {"min": 10, "max": 3000},
        "qm30_hf_a_x": {"min": 0, "max": 3000},
        "qm30_v_mm_y": {"min": 10, "max": 3000},
        "qm30_hf_a_y": {"min": 0, "max": 3000},
        "qm30_v_mm_z": {"min": 10, "max": 3000},
        "qm30_hf_a_z": {"min": 0, "max": 3000},
        "value_qm30_temp": {"min": 10, "max": 50},
        "value_b22_status": {"min": -1, "max": 2},
        "value_b22_peca": {"min": 10, "max": 9999},
        "s15cct_value": {"min": -1, "max": 9999},
    },
    "estufa": {
        "value_temp": {"min": 18, "max": 35},
        "value_humid": {"min": 30, "max": 80},
        "s24ASD_temperature": {"min": 18, "max": 35},
        "s24ASD_humidity": {"min": 30, "max": 80},
        "s24ASD_dewpoint": {"min": 5, "max": 25},
    },
    "tanque": {
        "value_q4x": {"min": -1, "max": 90}
    }
}


# Criação das tabelas no banco de dados e limpeza dos dados existentes
with app.app_context():
    db.create_all()
    db.session.query(SensorData).delete()
    db.session.commit()
    db.session.query(Alert).delete()
    db.session.commit()

# Configuração do dispositivo DXM
DXM_HOST = '192.168.0.1'
DXM_PORT = 502

# Inicialização do cliente Modbus para comunicação com o dispositivo DXM
client = ModbusClient(host=DXM_HOST, port=DXM_PORT, timeout=1)
reset = client.write_single_register(601, 1)
reset_o_reset = client.write_single_register(601, 0)

# Função para ler os dados dos sensores
def read_sensors():
    while not stop_event.is_set():  # Loop enquanto o evento de parada não for acionado

        time.sleep(0.5)

        with modbus_lock:

            if client.open():  # Verifica se a conexão com o dispositivo DXM está aberta
                q4x_s15c_i = client.read_holding_registers(405, 1)# Leitura dos registros dos sensores

                q4x_0_100 = ((q4x_s15c_i[0]-40)/160)*100  # Conversão do valor do sensor Q4

                th_rh_temp = client.read_holding_registers(100, 2)
                th_rh = th_rh_temp[0] / 100  # Umidade relativa
                th_temp = th_rh_temp[1] / 20  # Temperatura ambiente

                qm30_values = client.read_holding_registers(499, 9)
                qm30_v_mm_x = qm30_values[0]           # Velocidade X do sensor QM30
                qm30_hf_a_x = qm30_values[1]           # Aceleração X do sensor QM30
                qm30_v_mm_y = qm30_values[2]           # Velocidade Y do sensor QM30
                qm30_hf_a_y = qm30_values[3]           # Aceleração Y do sensor QM30
                qm30_v_mm_z = qm30_values[4]           # Aceleração Z do sensor QM30
                qm30_hf_a_z = qm30_values[5]           # Velocidade Z do sensor QM30
                qm30_temp_certo = qm30_values[6]/100   # Temperatura do sensor QM30
                qm30_remaining = qm30_values[7]/100    # Quantidade de samples restantes do sensor QM30

                b22_pin4_stats_pin2_count = client.read_holding_registers(599, 2)  # Status e Contagem de peças do sensor B22

                s15c_ct_value = (client.read_holding_registers(699, 1))[0] / 100 # Valores S15CT

                s24_values = client.read_holding_registers(799, 3)  # Valores S24 em C°
                s24_hum_corrigido = s24_values[0] / 100
                s24_temp_corrigido = s24_values[1] / 20
                s24_dp_corrigido = s24_values[2] / 100

                # Armazenamento dos dados no banco de dados
                with app.app_context():
                    new_data = SensorData(value_q4x=q4x_0_100,
                                          value_temp=th_temp, value_humid=th_rh,
                                          qm30_v_mm_x=qm30_v_mm_x, qm30_hf_a_x=qm30_hf_a_x,
                                          qm30_v_mm_y=qm30_v_mm_y, qm30_hf_a_y=qm30_hf_a_y,
                                          qm30_v_mm_z=qm30_v_mm_z, qm30_hf_a_z=qm30_hf_a_z,
                                          value_qm30_temp=qm30_temp_certo,
                                          value_b22_status=b22_pin4_stats_pin2_count[0], value_b22_peca=b22_pin4_stats_pin2_count[1],
                                          s15cct_value = s15c_ct_value,
                                          s24ASD_humidity = s24_hum_corrigido, s24ASD_temperature = s24_temp_corrigido,
                                          s24ASD_dewpoint = s24_dp_corrigido
                                          )
                    db.session.add(new_data)
                    db.session.commit()

                # Envio dos dados para o frontend via WebSocket
                socketio.emit('sensor_data', {
                                              'q4x': q4x_0_100, 'timestamp': datetime.utcnow().isoformat(),
                                              'value_temp': th_temp, 'value_humid': th_rh,
                                              'qm30_v_mm_x': qm30_v_mm_x, 'qm30_hf_a_x': qm30_hf_a_x,
                                              'qm30_v_mm_y': qm30_v_mm_y, 'qm30_hf_a_y': qm30_hf_a_y,
                                              'qm30_v_mm_z': qm30_v_mm_z, 'qm30_hf_a_z': qm30_hf_a_z,
                                              'value_qm30_temp': qm30_temp_certo, 'qm30_remaining': qm30_remaining,
                                              'value_b22_status': b22_pin4_stats_pin2_count[0], 'value_b22_peca': b22_pin4_stats_pin2_count[1],
                                              's15cct_value': s15c_ct_value,
                                              's24ASD_humidity' : s24_hum_corrigido, 's24ASD_temperature' : s24_temp_corrigido,
                                              's24ASD_dewpoint' : s24_dp_corrigido,
                                              'dxm': 'DXM está online :)'}, namespace='/')

                verificar_alertas("cnc", {
                    "qm30_v_mm_x": qm30_v_mm_x,
                    "qm30_hf_a_x": qm30_hf_a_x,
                    "qm30_v_mm_y": qm30_v_mm_y,
                    "qm30_hf_a_y": qm30_hf_a_y,
                    "qm30_v_mm_z": qm30_v_mm_z,
                    "qm30_hf_a_z": qm30_hf_a_z,
                    "value_qm30_temp": qm30_temp_certo,
                    "value_b22_status": b22_pin4_stats_pin2_count[0],
                    "value_b22_peca": b22_pin4_stats_pin2_count[1],
                    "s15cct_value": s15c_ct_value
                })

                verificar_alertas("estufa", {
                    "value_temp": th_temp,
                    "value_humid": th_rh,
                    "s24ASD_temperature": s24_temp_corrigido,
                    "s24ASD_humidity": s24_hum_corrigido,
                    "s24ASD_dewpoint": s24_dp_corrigido
                })

                verificar_alertas("tanque", {
                    "value_q4x": q4x_0_100
                })

                client.close()

            else:

                # Armazenamento dos dados no banco de dados
                with app.app_context():
                    new_data = SensorData(value_q4x=randint(0,99),
                                          value_temp=randint(0,99), value_humid=randint(0,99),
                                          qm30_v_mm_x=randint(0,99), qm30_hf_a_x=randint(0,99),
                                          qm30_v_mm_y=randint(0,99), qm30_hf_a_y=randint(0,99),
                                          qm30_v_mm_z=randint(0,99), qm30_hf_a_z=randint(0,99),
                                          value_qm30_temp=randint(0,99),
                                          value_b22_status=randint(0,1), value_b22_peca=randint(0,99),
                                          s15cct_value=randint(0,99),
                                          s24ASD_humidity=randint(0,99), s24ASD_temperature=randint(0,99),
                                          s24ASD_dewpoint=randint(0,99))
                    db.session.add(new_data)
                    db.session.commit()

                # Envio de dados padrão caso a conexão com o DXM falhe
                socketio.emit('sensor_data', {
                                              'q4x': randint(0,99), 'timestamp': datetime.utcnow().isoformat(),
                                              'value_temp': randint(0,99), 'value_humid': randint(0,99),
                                              'qm30_v_mm_x': randint(0,99), 'qm30_hf_a_x': randint(0,99),
                                              'qm30_v_mm_y': randint(0,99), 'qm30_hf_a_y': randint(0,99),
                                              'qm30_v_mm_z': randint(0,99), 'qm30_hf_a_z': randint(0,99),
                                              'value_qm30_temp': randint(0,99), 'qm30_remaining': 999,
                                              'value_b22_status': randint(0,1), 'value_b22_peca': randint(0,99),
                                              's15cct_value': randint(0,99),
                                              's24ASD_humidity' : randint(0,99), 's24ASD_temperature' : randint(0,99),
                                              's24ASD_dewpoint' : randint(0,99),
                                              'dxm': 'DXM está offline :('}, namespace='/')

                verificar_alertas("cnc", {
                    "qm30_v_mm_x": randint(0,99),
                    "qm30_hf_a_x": randint(0,99),
                    "qm30_v_mm_y": randint(0,99),
                    "qm30_hf_a_y": randint(0,99),
                    "qm30_v_mm_z": randint(0,99),
                    "qm30_hf_a_z": randint(0,99),
                    "value_qm30_temp": randint(0,99),
                    "s15cct_value": randint(0,99)
                })

                verificar_alertas("estufa", {
                    "value_temp": randint(0,99),
                    "value_humid": randint(0,99),
                    "s24ASD_temperature": randint(0,99),
                    "s24ASD_humidity": randint(0,99),
                    "s24ASD_dewpoint": randint(0,99)
                })

                verificar_alertas("tanque", {
                    "value_q4x": randint(0,99)
                })

def verificar_alertas(origem, dados_dict):

    with app.app_context():

        if origem not in LIMITES:
            return

        for parametro, valor in dados_dict.items():

            if parametro not in LIMITES[origem]:
                continue

            limite_min = LIMITES[origem][parametro]["min"]
            limite_max = LIMITES[origem][parametro]["max"]

            if valor < limite_min or valor > limite_max:

                alerta = Alert(
                    origem=origem,
                    parametro=parametro,
                    valor=valor,
                    limite_min=limite_min,
                    limite_max=limite_max
                )

                db.session.add(alerta)

        db.session.commit()

# Evento para parar a thread de leitura dos sensores
stop_event = threading.Event()

# Rotas do Flask para renderização das páginas HTML
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/cnc')
def cnc():
    return render_template('cnc.html')

@app.route('/agua')
def agua():
    return render_template('agua.html')

@app.route('/estufa')
def estufa():
    return render_template('estufa.html')

@app.route('/alertas/<origem>')
def pagina_alertas(origem):
    return render_template('alerta.html', origem=origem)

@app.route('/api/history/cnc')
def history_cnc():

    data = SensorData.query.order_by(
        SensorData.timestamp.desc()
    ).limit(20).all()

    data.reverse()

    return jsonify([
        {
            "timestamp": d.timestamp.isoformat(),
            "qm30_v_mm_x": d.qm30_v_mm_x,
            "qm30_hf_a_x": d.qm30_hf_a_x,
            "qm30_v_mm_y": d.qm30_v_mm_y,
            "qm30_hf_a_y": d.qm30_hf_a_y,
            "qm30_v_mm_z": d.qm30_v_mm_z,
            "qm30_hf_a_z": d.qm30_hf_a_z,
            "value_qm30_temp": d.value_qm30_temp,
            "value_b22_status": d.value_b22_status,
            "value_b22_peca": d.value_b22_peca,
            "s15cct_value": d.s15cct_value
        }
        for d in data
    ])

@app.route('/api/history/estufa')
def history_estufa():
    data = SensorData.query.order_by(
        SensorData.timestamp.desc()
    ).limit(20).all()

    data.reverse()

    return jsonify([
        {
            "timestamp": d.timestamp.isoformat(),
            "value_temp": d.value_temp,
            "value_humid": d.value_humid,
            "s24ASD_temperature": d.s24ASD_temperature,
            "s24ASD_humidity": d.s24ASD_humidity,
            "s24ASD_dewpoint": d.s24ASD_dewpoint
        }
        for d in data
    ])

@app.route('/api/alertas/<origem>')
def listar_alertas(origem):

    alertas = Alert.query.filter_by(origem=origem)\
        .order_by(Alert.timestamp.desc())\
        .all()

    return jsonify([
        {
            "id": a.id,
            "timestamp": a.timestamp.isoformat(),
            "parametro": a.parametro,
            "valor": a.valor,
            "limite_min": a.limite_min,
            "limite_max": a.limite_max,
            "lido": a.lido
        }
        for a in alertas
    ])

@app.route('/api/alerta/<int:id>/lido', methods=['POST'])
def marcar_lido(id):

    alerta = Alert.query.get_or_404(id)
    alerta.lido = True
    db.session.commit()

    return jsonify({"status": "ok"})

@app.route('/api/alerta/<int:id>', methods=['DELETE'])
def excluir_alerta(id):

    alerta = Alert.query.get_or_404(id)
    db.session.delete(alerta)
    db.session.commit()

    return jsonify({"status": "excluido"})

@app.route('/api/alertas/<origem>/apagar_todos', methods=['DELETE'])
def apagar_todos(origem):

    Alert.query.filter_by(origem=origem).delete()

    db.session.commit()

    return jsonify({"status": "todos_apagados"})

@app.route('/api/alertas/<origem>/ler_todos', methods=['POST'])
def marcar_todos_lido(origem):

    Alert.query.filter_by(origem=origem, lido=False)\
        .update({"lido": True})

    db.session.commit()

    return jsonify({"status": "todos_lidos"})


@app.route("/api/limites", methods=["POST"])
def atualizar_limites():
    data = request.json

    setor = data.get("setor")
    variavel = data.get("variavel")
    minimo = data.get("min")
    maximo = data.get("max")

    if setor in LIMITES and variavel in LIMITES[setor]:
        LIMITES[setor][variavel]["min"] = minimo
        LIMITES[setor][variavel]["max"] = maximo
        return jsonify({"status": "ok"})

    return jsonify({"status": "erro"}), 400

@app.route("/api/limites/<setor>/<variavel>")
def get_limites(setor, variavel):
    if setor in LIMITES and variavel in LIMITES[setor]:
        return jsonify(LIMITES[setor][variavel])
    return jsonify({"erro": "não encontrado"}), 404

@app.route("/api/status_maquinas")
def status_maquinas():

    status = {
        "cnc": "normal",
        "estufa": "normal",
        "tanque": "normal"
    }

    maquinas = ["cnc", "estufa", "tanque"]

    for maquina in maquinas:
        alerta_existente = Alert.query.filter_by(
            origem=maquina,
            lido=False
        ).first()

        if alerta_existente:
            status[maquina] = "alerta"

    return jsonify(status)

def monitorar_treinamento_qm30():

    global treinamento_qm30_ativo
    global qm30_remain_treinamento

    while True:
        with modbus_lock:
            if client.open():
                rr = client.read_holding_registers(506, 1)
                ready = client.read_holding_registers(524, 1)
                print(ready[0])

            if rr:
                qm30_remain_treinamento = rr[0]

                socketio.emit("qm30_training_status", {
                    "remain": qm30_remain_treinamento
                })

                if ready[0] == 4:
                    break

        time.sleep(1)

    with modbus_lock:
        if client.open():
            novos_limites = client.read_holding_registers(509, 14)

        if novos_limites:
            LIMITES["cnc"]["qm30_v_mm_x"]["min"] = novos_limites[0]
            LIMITES["cnc"]["qm30_v_mm_x"]["max"] = novos_limites[6]

            LIMITES["cnc"]["qm30_v_mm_y"]["min"] = novos_limites[1]
            LIMITES["cnc"]["qm30_v_mm_y"]["max"] = novos_limites[7]

            LIMITES["cnc"]["qm30_v_mm_z"]["min"] = novos_limites[2]
            LIMITES["cnc"]["qm30_v_mm_z"]["max"] = novos_limites[8]

            LIMITES["cnc"]["qm30_hf_a_x"]["min"] = novos_limites[3]
            LIMITES["cnc"]["qm30_hf_a_x"]["max"] = novos_limites[9]

            LIMITES["cnc"]["qm30_hf_a_y"]["min"] = novos_limites[4]
            LIMITES["cnc"]["qm30_hf_a_y"]["max"] = novos_limites[10]

            LIMITES["cnc"]["qm30_hf_a_z"]["min"] = novos_limites[5]
            LIMITES["cnc"]["qm30_hf_a_z"]["max"] = novos_limites[11]

            LIMITES["cnc"]["value_qm30_temp"]["min"] = novos_limites[12]
            LIMITES["cnc"]["value_qm30_temp"]["max"] = novos_limites[13]

    treinamento_qm30_ativo = False

    socketio.emit("qm30_training_status", {
        "remain": 0,
        "finalizado": True
    })

@app.route("/api/executar_acao_cnc", methods=["POST"])
def executar_treinamento_qm30():

    global treinamento_qm30_ativo

    if treinamento_qm30_ativo:
        return jsonify({"status": "treinamento_em_execucao"})

    treinamento_qm30_ativo = True

    with modbus_lock:
        if client.open():
            client.write_single_register(507, 1)
            time.sleep(1)
            client.write_single_register(507, 0)
            time.sleep(2)

    thread = threading.Thread(target=monitorar_treinamento_qm30)
    thread.daemon = True
    thread.start()

    return jsonify({"status": "treinamento_iniciado"})
# Rota para ‘download’ dos dados em formato Excel
@app.route('/download', methods=['POST'])
def download():
    data = request.form.get('button')
    dbq = SensorData.query.all()
    if data == 'agua':
        json_file = [{'timestamp': d.timestamp.isoformat(), 'q4x': d.value_q4x} for d in dbq]

    elif data == 'cnc':
        json_file = [{'timestamp': d.timestamp.isoformat(),
                      'qm30_hf_aceleracao_z': d.qm30_hf_a_z, 'qm30_velocidade_mm_z': d.qm30_v_mm_z,
                      'qm30_hf_aceleracao_x': d.qm30_hf_a_x, 'qm30_velocidade_mm_x': d.qm30_v_mm_x,
                      'qm30_hf_aceleracao_y': d.qm30_hf_a_y, 'qm30_velocidade_mm_y': d.qm30_v_mm_y,
                      'value_qm30_temp': d.value_qm30_temp, 's15c_valor_corrente': d.s15c_ct,
                      'value_b22_status_pin4': d.value_b22_status, 'value_b22_peca_pin2': d.value_b22_peca} for d in dbq]

    elif data == 'estufa':
        json_file = [{'timestamp': d.timestamp.isoformat(), 's15_temperatura': d.value_temp, 's15_humiddade': d.value_humid,
                      's24ASD_umidade': d.s24ASD_humidity, 's24ASD_temperatura': d.s24ASD_temperature, 's24ASD_ponto_orvalho': d.s24ASD_dewpoint
                      } for d in dbq]

    df = pd.DataFrame(json_file)
    df.to_excel("excel.xlsx", index=False)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        writer._save()

    output.seek(0)

    # Retorna o arquivo para download
    return send_file(output, download_name="excel.xlsx", as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# Rota para o favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'images/favicon.ico', mimetype='image/vnd.microsoft.icon')

# Função para iniciar o aplicativo Flask
def start_flask_app():
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)

# Função para iniciar a interface gráfica (GUI) usando customtkinter
def start_gui():
    customtkinter.set_appearance_mode("dark")
    root = customtkinter.CTk()
    root.title("Inicializador do Flask")
    root.geometry("400x200")

    def open_browser():
        webbrowser.open("http://localhost:5000")

    def on_closing():
        stop_event.set()  # Sinaliza a parada da thread do Flask
        root.destroy()  # Fecha a janela Tkinter

    root.protocol("WM_DELETE_WINDOW", on_closing)

    button = customtkinter.CTkButton(root, text="Abrir Dashboard", command=open_browser, anchor="center")
    button.pack(pady=20)

    root.mainloop()

# Ponto de entrada do aplicativo
if __name__ == "__main__":
    read = threading.Thread(target=read_sensors)
    read.start()

    flask_thread = threading.Thread(target=start_flask_app)
    flask_thread.daemon = True
    flask_thread.start()
    start_gui()