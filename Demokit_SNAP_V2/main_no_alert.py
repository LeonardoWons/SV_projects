# Importações necessárias para o funcionamento do aplicativo
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
import time
import os

# Inicialização do aplicativo Flask
app = Flask(__name__)

# Configuração do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sensores.db'
db = SQLAlchemy(app)

# Inicialização do SocketIO para comunicação em tempo real
socketio = SocketIO(app, cors_allowed_origins="*")

timestamp = datetime.now(timezone.utc)

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


# Criação das tabelas no banco de dados e limpeza dos dados existentes
with app.app_context():
    db.create_all()
    db.session.query(SensorData).delete()
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
        time.sleep(.2)

        if client.open():  # Verifica se a conexão com o dispositivo DXM está aberta
            # Leitura dos registros dos sensores
            q4x_s15c_i = client.read_holding_registers(405, 1)

            q4x_0_100 = ((q4x_s15c_i[0]-40)/160)*100  # Conversão do valor do sensor Q4

            th_rh_temp = client.read_holding_registers(100, 2)
            th_rh = th_rh_temp[0] / 100  # Umidade relativa
            th_temp = th_rh_temp[1] / 20  # Temperatura ambiente

            qm30_values = client.read_holding_registers(500, 7)
            qm30_v_mm_x = qm30_values[0] / 1000  # Velocidade X do sensor QM30
            qm30_hf_a_x = qm30_values[1] / 1000  # Aceleração X do sensor QM30
            qm30_v_mm_y = qm30_values[2] / 1000  # Velocidade Y do sensor QM30
            qm30_hf_a_y = qm30_values[3] / 1000  # Aceleração Y do sensor QM30
            qm30_hf_a_z = qm30_values[4] / 1000  # Aceleração Z do sensor QM30
            qm30_v_mm_z = qm30_values[5] / 1000  # Velocidade Z do sensor QM30
            qm30_temp_certo = qm30_values[6] / 10  # Temperatura do sensor QM30

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
                                          'value_qm30_temp': qm30_temp_certo,
                                          'value_b22_status': b22_pin4_stats_pin2_count[0], 'value_b22_peca': b22_pin4_stats_pin2_count[1],
                                          's15cct_value': s15c_ct_value,
                                          's24ASD_humidity' : s24_hum_corrigido, 's24ASD_temperature' : s24_temp_corrigido,
                                          's24ASD_dewpoint' : s24_dp_corrigido,
                                          'dxm': 'DXM está online :)'}, namespace='/')

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
                                          'value_qm30_temp': randint(0,99),
                                          'value_b22_status': randint(0,1), 'value_b22_peca': randint(0,99),
                                          's15cct_value': randint(0,99),
                                          's24ASD_humidity' : randint(0,99), 's24ASD_temperature' : randint(0,99),
                                          's24ASD_dewpoint' : randint(0,99),
                                          'dxm': 'DXM está offline :('}, namespace='/')

# Evento para parar a thread de leitura dos sensores
stop_event = threading.Event()

# Inicialização da thread para leitura dos sensores
threading.Thread(target=read_sensors).start()

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
    flask_thread = threading.Thread(target=start_flask_app)
    flask_thread.daemon = True
    flask_thread.start()
    start_gui()