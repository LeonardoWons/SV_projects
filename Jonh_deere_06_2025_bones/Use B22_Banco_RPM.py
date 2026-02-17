import time
from pymodbus.client import ModbusSerialClient

# Configuração do Modbus
client = ModbusSerialClient(port='COM12', baudrate=19200, timeout=1)
slave_id = 4  # Endereço do sensor
numero_dentes = 4

if not client.connect():
    print("Erro ao conectar no sensor B22.")
    exit()

try:
    while True:
        # Leitura do registrador de CPM do PINO 2
        result = client.read_holding_registers(40022, slave=slave_id)
        if not result.isError():
            cpm = result.registers[0]
            rpm = cpm / numero_dentes  # 4 pulsos por giro
            print(f"CPM: {cpm} | RPM: {rpm:.2f}")
        else:
            print("Erro ao ler CPM do sensor.")

        client.write_register(40400, 1, slave=slave_id)

        time.sleep(1)  # atualiza a cada 1 segundo

        client.write_register(40400, 0, slave=slave_id)

        time.sleep(1)

except KeyboardInterrupt:
    print("\nMonitoramento finalizado.")

finally:
    client.close()
