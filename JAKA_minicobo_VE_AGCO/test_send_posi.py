from pymodbus.client import ModbusTcpClient
import socket
import struct

# Conectar na câmera (MODBUS/TCP)
camera_ip = "10.5.5.110"
client = ModbusTcpClient(camera_ip, port=502)
client.connect()

# Ler registrador da câmera
rr = client.read_holding_registers(address=1021, count=4)

lsw_x = rr.registers[0]
msw_x = rr.registers[1]
lsw_y = rr.registers[2]
msw_y = rr.registers[3]

# Inverter ordem para MSW:LSW (para formar float correto)
raw_x = struct.pack('>HH', msw_x, lsw_x)  # MSW primeiro, depois LSW
x_value = struct.unpack('>f', raw_x)[0]

# Inverter ordem para MSW:LSW (para formar float correto)
raw_y = struct.pack('>HH', msw_y, lsw_y)  # MSW primeiro, depois LSW
y_value = struct.unpack('>f', raw_y)[0]

print(round(x_value, 2))
print(round(y_value, 2))

client.close()

HOST = '0.0.0.0'        # Aceita conexão de qualquer IP
PORT_X = 1000             # Porta que o robô vai usar
PORT_Y = 1001             # Porta que o robô vai usar

while True:

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT_X))
        server.listen(1)
        print(f"Posição X na porta {PORT_X}...")

        connx, addrx = server.accept()
        with connx:
            print(x_value)
            formated_x_value = round(x_value,2)
            mensagem = f'<X><{formated_x_value}>'
            connx.sendall(mensagem.encode())
            print(f"Enviado: {mensagem.strip()}")


    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT_Y))
        server.listen(1)
        print(f"Posição Y na porta {PORT_Y}...")

        conny, addry = server.accept()
        with conny:
            print(y_value)
            mensagem = f"<yy>< {y_value} >"
            conny.sendall(mensagem.encode())
            print(f"Enviado: {mensagem.strip()}")



