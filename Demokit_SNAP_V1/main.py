# Importações necessárias para o funcionamento do aplicativo
from flask import Flask, render_template, send_from_directory, jsonify, request, send_file
from pyModbusTCP.client import ModbusClient
from flask_sqlalchemy import SQLAlchemy
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

# Definição do modelo de dados para armazenar as leituras dos sensores
class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
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

    S24ASD_humidity = db.Column(db.Integer)  # Humidade ambiente
    S24ASD_temperature = db.Column(db.Integer)  # Temperatura ambiente
    S24ASD_dewpoint = db.Column(db.Integer)  # DewPoint ambiente

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
        time.sleep(1)

        if client.open():  # Verifica se a conexão com o dispositivo DXM está aberta
            # Leitura dos registros dos sensores
            q4x_s15c_i = client.read_holding_registers(405, 1)
            q4x_0_100 = ((q4x_s15c_i[0] - 40)/160)*100  # Conversão do valor do sensor Q4X

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

            b22_pin4_stats = client.read_holding_registers(599, 1)  # Status do sensor B22
            b22_pin4_total = client.read_holding_registers(600, 1)  # Contagem de peças do sensor B22

            # Armazenamento dos dados no banco de dados
            with app.app_context():
                new_data = SensorData(value_q4x=q4x_0_100,
                                      qm30_hf_a_z=qm30_hf_a_z, qm30_hf_a_x=qm30_hf_a_x,
                                      qm30_v_mm_z=qm30_v_mm_z, qm30_v_mm_x=qm30_v_mm_x,
                                      value_qm30_temp=qm30_temp_certo,
                                      value_b22_status=b22_pin4_stats[0], value_b22_peca=b22_pin4_total[0],
                                      value_temp=th_temp, value_humid=th_rh)
                db.session.add(new_data)
                db.session.commit()

            # Envio dos dados para o frontend via WebSocket
            socketio.emit('sensor_data', {'q4x': q4x_0_100,
                                          'qm30_hf_a_z': qm30_hf_a_z, 'qm30_hf_a_x': qm30_hf_a_x,
                                          'qm30_v_mm_z': qm30_v_mm_z, 'qm30_v_mm_x': qm30_v_mm_x,
                                          'value_qm30_temp': qm30_temp_certo,
                                          'value_b22_status': b22_pin4_stats[0], 'value_b22_peca': b22_pin4_total[0],
                                          'value_temp': th_temp, 'value_humid': th_rh,
                                          'dxm': 'DXM está online :)'}, namespace='/')

            client.close()

        else:
            # Envio de dados padrão caso a conexão com o DXM falhe
            socketio.emit('sensor_data', {'q4x': 0,
                                          'qm30_hf_a_z': 0, 'qm30_hf_a_x': 0,
                                          'qm30_v_mm_z': 0, 'qm30_v_mm_x': 0,
                                          'value_qm30_temp': 0,
                                          'value_b22_status': 0, 'value_b22_peca': 0,
                                          'value_temp': 0, 'value_humid': 0,
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

@app.route('/sala')
def sala():
    return render_template('sala.html')

# Rotas para API que fornecem dados para o frontend
@app.route('/api/data/agua')
def get_data():
    with app.app_context():
        data = SensorData.query.order_by(SensorData.timestamp.desc()).limit(20).all()
        data.reverse()  # Reverter para ordem cronológica
        return jsonify([{'timestamp': d.timestamp, 'value': d.value_q4x} for d in data])

@app.route('/api/data/tempo_medio_peca')
def get_tempo_medio_peca():
    first_record = SensorData.query.order_by(SensorData.timestamp.asc()).first()
    last_record = SensorData.query.order_by(SensorData.timestamp.desc()).first()

    if first_record and last_record:
        delta_time = int((last_record.timestamp - first_record.timestamp).total_seconds())
        total_pecas = last_record.value_b22_peca

        if total_pecas > 0 and delta_time > 0:
            tempo_medio_peca = total_pecas / delta_time
            percentual_diferenca = tempo_medio_peca
        else:
            percentual_diferenca = 0

        return jsonify({'percentual_diferenca': round(percentual_diferenca, 1)})

    return jsonify({'tempo_medio_peca': 0, 'percentual_diferenca': 0})

@app.route('/api/data/status_difference')
def get_status_difference():
    with app.app_context():
        total_status_1 = SensorData.query.filter_by(value_b22_status=1).count()
        total_records = SensorData.query.count()

        if total_records > 0 and total_status_1 > 0:
            percentual_difference = (total_status_1 / total_records) * 100
        else:
            percentual_difference = 0

        return jsonify({
            'percentual_difference': round(percentual_difference, 2)
        })

@app.route('/api/data/sala')
def get_data_sala():
    with app.app_context():
        data = SensorData.query.order_by(SensorData.timestamp.desc()).limit(5).all()
        data.reverse()  # Reverter para ordem cronológica
        return jsonify([{'timestamp': d.timestamp, 'temp': d.value_temp, 'humid': d.value_humid} for d in data])

# Rota para ‘download’ dos dados em formato Excel
@app.route('/download', methods=['POST'])
def download():
    data = request.form.get('button')
    dbq = SensorData.query.all()
    if data == 'agua':
        json_file = [{'timestamp': d.timestamp, 'q4x': d.value_q4x} for d in dbq]

    elif data == 'cnc':
        json_file = [{'timestamp': d.timestamp,
                      'qm30_hf_aceleracao_z': d.qm30_hf_a_z, 'qm30_hf_aceleracao_x': d.qm30_hf_a_x,
                      'qm30_velocidade_mm_z': d.qm30_v_mm_z, 'qm30_velocidade_mm_x': d.qm30_v_mm_x,
                      'value_qm30_temp': d.value_qm30_temp,
                      'value_b22_status_pin4': d.value_b22_status, 'value_b22_peca_pin2': d.value_b22_peca} for d in dbq]

    elif data == 'sala':
        json_file = [{'timestamp': d.timestamp, 'temperatura': d.value_temp, 'humiddade': d.value_humid} for d in dbq]

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