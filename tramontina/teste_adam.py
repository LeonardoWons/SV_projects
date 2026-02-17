from pymodbus.client import ModbusTcpClient

# ADAM-6050
ADAM_IP = "10.16.135.21"
ADAM_PORT = 502
DI_ADDR = 0     # Entrada 1 → endereço 00001
DO2_ADDR = 17    # Saída 2 → endereço 00018


# Modbus
client = ModbusTcpClient(ADAM_IP, port=ADAM_PORT)

client.connect()

client.write_coil(17, 1)

client.close()
