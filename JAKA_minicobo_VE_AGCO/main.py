import os
import time
import fitz
import struct
import socket
from io import BytesIO
from threading import Thread
from threading import Event
from datetime import datetime
from PIL import Image
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
from flask import Flask, render_template, jsonify, send_from_directory

botao_event = Event()

class RobotController:
    def __init__(self, ip):
        self.client = ModbusTcpClient(ip, port=6502)
        self.slave_id = 1
        self.di_address = 40 #di_address 40 = 1, 41 = 2 ...
        self.do_address = 8 #do_address 8 = 1, 9 = 2 ...

    def connect(self):
        return self.client.connect()

    def disconnect(self):
        self.client.close()

    def reset_di_robot(self):
        for n in range(4):
            self.client.write_coil(address=self.di_address + n, value=False, slave=self.slave_id)

    def reset_position(self):
        self.client.write_coil(address=44, value=True, slave=self.slave_id)
        time.sleep(0.5)
        self.client.write_coil(address=44, value=False, slave=self.slave_id)

    def inspection_step(self, inspecao):
        try:
            self.client.write_coil(address=self.di_address + inspecao, value=True, slave=self.slave_id)

            print(f"Sinal enviado para DI {self.di_address + inspecao}")
            print(f"Aguardando confirmação em DO {self.do_address + inspecao}...")

            host = '0.0.0.0'
            port_x = 1000
            port_y = 1001

            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                    server.bind((host, port_x))
                    server.listen(1)
                    print(f"Posição X na porta {port_x}...")

                    connx, addrx = server.accept()
                    with connx:
                        mensagem = f"<X><{round(x_value,2)}>"
                        connx.sendall(mensagem.encode())
                        print(f"Enviado: {mensagem.strip()}")
            except Exception as e:
                print(e)

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                server.bind((host, port_y))
                server.listen(1)
                print(f"Posição Y na porta {port_y}...")

                conny, addry = server.accept()
                with conny:
                    mensagem = f"<Y><{round(y_value,2)}>"
                    conny.sendall(mensagem.encode())
                    print(f"Enviado: {mensagem.strip()}")

            for _ in range(1000):
                response = self.client.read_discrete_inputs(address=self.do_address + inspecao, count=1, slave=self.slave_id)
                if response and bool(response.bits[0]):
                    self.client.write_coil(address=self.di_address + inspecao, value=False, slave=self.slave_id)
                    return True
                time.sleep(0.1)

        except (ConnectionError, ModbusException) as e:
            print(f"Erro Modbus: {e}")
            return False

class CameraImageReceiver:
    def __init__(self, ip):
        self.ip = ip
        self.save_dir = "static"
        self.resize_scale = 0.28

        self.client = ModbusTcpClient(self.ip, port=502)
        self.results = None
        self.line_color = "red"

    def receive_image(self, inspection):
        try:
            with socket.create_connection((self.ip, 32200), timeout=1000) as sock:
                print("📷 Recebendo imagem...")
                resultados_formatados = []

                buffer = b""
                while True:
                    data = sock.recv(4096)
                    if not data:
                        break
                    buffer += data

                    start = buffer.find(b'\xff\xd8')
                    end = buffer.find(b'\xff\xd9')

                    if start != -1 and end != -1 and end > start:
                        jpeg_data = buffer[start:end + 2]
                        break

                image = Image.open(BytesIO(jpeg_data))


                new_size = (int(image.width * self.resize_scale), int(image.height * self.resize_scale))
                image = image.resize(new_size)

                filename = f"{inspection}.jpeg"
                filepath = os.path.join(self.save_dir, filename)
                image.save(filepath, format="JPEG")
                print(f"✅ Imagem salva: {filepath}")

                n = 4 - sum(self.results)

                texto = f'{n}/4 Parafusos'
                resultados_formatados.append(texto)

                return resultados_formatados

        except Exception as e:
            print(f"Erro ao receber imagem: {e}")

    def inspection_result(self):
        global x_value
        global y_value

        if self.client.connect():
            try:
                result = self.client.read_holding_registers(address=1017, count=8).registers
                self.results = result[:4]
                rr = result[4:]

                lsw_x = rr[0]
                msw_x = rr[1]
                lsw_y = rr[2]
                msw_y = rr[3]

                # Inverter ordem para MSW:LSW (para formar float correto)
                raw_x = struct.pack('>HH', msw_x, lsw_x)  # MSW primeiro, depois LSW
                x_value = struct.unpack('>f', raw_x)[0]
                #x_value -= 50


                # Inverter ordem para MSW:LSW (para formar float correto)
                raw_y = struct.pack('>HH', msw_y, lsw_y)  # MSW primeiro, depois LSW
                y_value = struct.unpack('>f', raw_y)[0]
                #y_value += 10


            except Exception as e:
                print(f"Erro ao ler resultado: {e}")
                self.results = None
            self.client.close()
        else:
            print('erro a conectar')

def gerar_pdf_com_imagens_e_texto(img_path, textos):
    doc = fitz.open("PDF_model.pdf")
    page = doc[0]

    posicoes = [(30, 155), (312, 155), (30, 475), (312, 475)]

    largura_max = 250  # em pontos (ex: 200 pts ~7cm)

    for i in range(len(img_path)):
        x, y = posicoes[i % len(posicoes)]

        # Abrir imagem com PIL para obter tamanho
        img = Image.open(img_path[i])
        largura_original, altura_original = img.size

        # Reduz proporcionalmente para a largura máxima
        if largura_original > largura_max:
            escala = largura_max / largura_original
            nova_largura = largura_original * escala
            nova_altura = altura_original * escala
        else:
            nova_largura = largura_original
            nova_altura = altura_original

        rect = fitz.Rect(x, y, x + nova_largura, y + nova_altura)
        page.insert_image(rect, filename=img_path[i])

        # Inserir os textos abaixo da imagem
        for t in range(4):
            texto_y = y + nova_altura + 21 * (t + 1)
            page.insert_text((x, texto_y), textos[i][t], fontsize=17, fontname="helv", color=(0, 0, 0))

    doc.save("static/Resultado.pdf")
    doc.close()
    print("✅ PDF salvo: Resultado.pdf" )

#SETUP
app = Flask(__name__)
robot = RobotController(ip='10.5.5.100')
camera = CameraImageReceiver(ip="10.5.5.110")

global x_value
global y_value

inspecoes = ['Parafuso_1', 'Parafuso_2', 'Parafuso_3', 'Parafuso_4']
imgs_paths = [f"static/{i}.jpeg" for i in inspecoes]
textos_img = [['Data:', 'Resultado:', f'Inspeção: {insp}', 'Modelo: SV MADE'] for insp in inspecoes]

@app.route("/")
def home():
    return render_template("index.html", inspecoes=inspecoes)

@app.route("/dados")
def dados():
    return jsonify(textos_img)

@app.route('/static/<path:filename>')
def serve_image(filename):
    return send_from_directory('static', filename)

@app.route('/botao', methods=['POST'])
def botao():
    print("✅ Botão foi apertado!")
    botao_event.set()  # Libera o processo
    return "Botão apertado com sucesso!"

def executar_rotina_inspecao():
    if robot.connect():
        robot.reset_di_robot()
        try:
            print("entrou try")
            while True:
                print("while")
                time.sleep(1)
                for i, insp in enumerate(inspecoes):
                    print(f"\n🔍 Etapa {insp}")
                    robot.reset_position()
                    print("reset robot position")
                    botao_event.wait()
                    botao_event.clear()
                    camera.inspection_result()
                    robot.inspection_step(i)
                    result = camera.receive_image(insp)
                    if result:
                        textos_img[i][0] = f"Data: {datetime.now().strftime('%d/%m/%y %H:%M')}"
                        textos_img[i][1] = f"Resultado: {result}"
                    else:
                        print("❌ Falha na inspeção. Encerrando.")
                        continue
                gerar_pdf_com_imagens_e_texto(imgs_paths, textos_img)
                time.sleep(10)
                robot.reset_di_robot()
        except Exception as e :
            print(e)
            robot.disconnect()
    else:
        print("❌ Falha ao conectar com robô")

if __name__ == "__main__":
    Thread(target=executar_rotina_inspecao).start()
    app.run(debug=False, host="0.0.0.0")

