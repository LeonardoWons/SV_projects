import os
import time
import fitz
import socket
from io import BytesIO
from threading import Thread
from datetime import datetime
from PIL import Image, ImageDraw
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
from flask import Flask, render_template, jsonify, send_from_directory

class RobotController:
    def __init__(self, ip):
        self.client = ModbusTcpClient(ip, port=6502)
        self.slave_id = 1
        self.di_address = 40
        self.do_address = 8

    def connect(self):
        return self.client.connect()

    def disconnect(self):
        self.client.close()

    def reset_di_robot(self):
        for n in range(4):
            self.client.write_coil(address=self.di_address + n, value=False, slave=self.slave_id)

    def inspection_step(self, inspecao):
        try:
            self.client.write_coil(address=self.di_address + inspecao, value=True, slave=self.slave_id)
            print(f"Sinal enviado para DI {self.di_address + inspecao}")
            print(f"Aguardando confirmação em DO {self.do_address + inspecao}...")

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
        self.slave_id = 0
        self.address = 1017
        self.results = None
        self.line_color = "red"

    def receive_image(self, inspection):
        try:
            with socket.create_connection((self.ip, 32200), timeout=1000) as sock:
                print("📷 Recebendo imagem...")
                resultados_formatados = []

                self.inspection_result()

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

                if self.resize_scale:
                    new_size = (int(image.width * self.resize_scale), int(image.height * self.resize_scale))
                    image = image.resize(new_size)

                filename = f"{inspection}.jpeg"
                filepath = os.path.join(self.save_dir, filename)
                image = image.convert("RGB")
                draw = ImageDraw.Draw(image)
                draw.rectangle([(40,40), (100, 200)], outline=self.line_color, width=3)
                image.save(filepath, format="JPEG")
                print(f"✅ Imagem salva: {filepath}")

                for resultado in self.results:
                    texto = " | ".join("Aprovado" if val == 1 else "Reprovado" for val in resultado)
                    resultados_formatados.append(texto)

                return resultados_formatados

        except Exception as e:
            print(f"Erro ao receber imagem: {e}")

    def inspection_result(self):
        if self.client.connect():
            try:
                self.results = self.client.read_holding_registers(address=self.address, count=4).registers
                print(self.results)
                if self.results == [1, 1, 1, 1]:
                    self.line_color = "green"
                else:
                    self.line_color = "red"
            except Exception as e:
                print(f"Erro ao ler resultado: {e}")
                self.results = None
            self.client.close()
        else:
            print('erro a conectar')

def gerar_pdf_com_imagens_e_texto(img_path, textos):
    doc = fitz.open("PDF_model.pdf")
    page = doc[0]

    posicoes = [(30, 155), (312, 155), (30, 167), (312, 167)]

    for i in range(len(img_path)):
        x, y = posicoes[i % len(posicoes)]
        img = Image.open(img_path[i])
        rect = fitz.Rect(x, y, x + img.width, y + img.height)
        page.insert_image(rect, filename=img_path[i])
        for t in range(4):
            page.insert_text((x, y + img.height + 21*(t+1)), textos[i][t], fontsize=17, fontname="helv", color=(0, 0, 0))

    doc.save("Resultado Inspeção.pdf")
    doc.close()
    print("✅ PDF salvo: Resultado Inspeção.pdf" )

# FLASK SETUP
app = Flask(__name__)
robot = RobotController(ip='10.5.5.100')
camera = CameraImageReceiver(ip="10.5.5.110")

inspecoes = ['Parafuso 1', 'Parafuso 2', 'Parafuso 3', 'Parafuso 4']
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
    print("Botão foi apertado!")
    # Coloque sua lógica aqui
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
                    #colocar o wait do botão apertado aqui
                    result = camera.receive_image(insp)
                    if result:
                        robot.inspection_step(i)
                        textos_img[i][0] = f"Data: {datetime.now().strftime('%d/%m/%y %H:%M')}"
                        textos_img[i][1] = f"Resultado: {result}"
                    else:
                        print("❌ Falha na inspeção. Encerrando.")
                        continue
                gerar_pdf_com_imagens_e_texto(imgs_paths, textos_img)
                robot.reset_di_robot()
                time.sleep(10)
        except Exception as e :
            print(e)
            robot.disconnect()
    else:
        print("❌ Falha ao conectar com robô")

if __name__ == "__main__":
    Thread(target=executar_rotina_inspecao).start()
    #app.run(debug=True, host="0.0.0.0")

