import time
from pymodbus.client import ModbusSerialClient

# Configuração do Modbus
client = ModbusSerialClient(port='COM11', baudrate=19200, timeout=1)
slave_id = 3  # Endereço do sensor

if not client.connect():
    print("Erro ao conectar no sensor B22.")
    exit()

while True:
    result = client.read_holding_registers(40001, slave=slave_id, count=2)
    print("pin2: "+str(result.registers[0]))
    print("pin4: "+str(result.registers[1]))
    print("\n")
    time.sleep(.2)
    result = client.read_holding_registers(40001, slave=3, count=2)
    print("pin2: " + str(result.registers[0]))
    print("pin4: " + str(result.registers[1]))
    print("\n")
    time.sleep(.2)

"""try:
    while True:
        # Leitura do registrador de CPM do PINO 2
        result = client.read_holding_registers(40001, slave=slave_id, count=2)
        print(result.registers[0])
        print(result.registers[1])
        time.sleep(1)  # atualiza a cada 1 segundo

except KeyboardInterrupt:
    print("\nMonitoramento finalizado.")

finally:
    client.close()
"""