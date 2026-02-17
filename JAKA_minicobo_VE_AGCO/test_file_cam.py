import socket
import os
from datetime import datetime
from PIL import Image, ImageDraw
from io import BytesIO
from pymodbus.client import ModbusTcpClient


class CameraImageReceiver:
    def __init__(self):
        self.ip = "10.5.5.110"
        self.port = 502
        self.save_dir = "captured_images"
        self.resize_scale = 0.5
        os.makedirs(self.save_dir, exist_ok=True)

        self.client = ModbusTcpClient(self.ip, port=self.port)
        self.slave_id = 0
        self.address = 1017
        self.results = None
        self.line_color = "red"

    def receive_image(self):
        try:
            with socket.create_connection((self.ip, 32200), timeout=10) as sock:
                print("📷 Conectado à câmera. Recebendo imagem...")

                self.inspection_result()

                # Lê dados da imagem
                buffer = b""
                while True:
                    data = sock.recv(4096)
                    if not data:
                        break
                    buffer += data

                    # Encontra delimitadores JPEG
                    start = buffer.find(b'\xff\xd8')  # SOI
                    end = buffer.find(b'\xff\xd9')  # EOI

                    if start != -1 and end != -1 and end > start:
                        jpeg_data = buffer[start:end + 2]
                        break

                # Processa imagem
                image = Image.open(BytesIO(jpeg_data))

                # Redimensiona se necessário
                if self.resize_scale:
                    width, height = image.size
                    print(image.size)
                    new_size = (int(width * self.resize_scale), int(height * self.resize_scale))
                    image = image.resize(new_size)
                    print(f"🖼️ Imagem redimensionada para: {new_size}")

                # Salva imagem com timestamp
                filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
                filepath = os.path.join(self.save_dir, filename)
                image = image.convert("RGB")
                img_square = ImageDraw.Draw(image)
                img_square.rectangle([(40,40), (100, 200)], outline=self.line_color, width=3)
                image.save(filepath, format="JPEG")
                print(f"✅ Imagem salva: {filepath}")

        except Exception as e:
            print(f"❌ Erro ao receber imagem: {e}")

    def inspection_result(self):
        self.client.connect()

        try:
            self.results = self.client.read_holding_registers(address=self.address, count=2)
            print(self.results)
            if self.results == [1,1]:
                self.line_color = "green"
            else:
                self.line_color = "red"

        except Exception as e:
            print(f"❌ Erro ao receber resultados: {e}")
            self.results = None

        self.client.close()
