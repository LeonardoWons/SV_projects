import time
from pymodbus.client import ModbusSerialClient

while True:
    try:
        # Configuração do Modbus
        client = ModbusSerialClient(port='COM18', baudrate=19200, timeout=1)
        slave_id = 4  # Endereço do sensor
        numero_dentes = 4

        while True:
            # Leitura do registrador de CPM do PINO 2
            result = client.read_holding_registers(40001, count=2, slave=slave_id)
            print(result.registers)

            client.write_register(40400, 1, slave=slave_id)

            time.sleep(.1)  # atualiza a cada 1 segundo

            #client.write_register(40400, 0, slave=slave_id)

            #time.sleep(1)

    except:
        print("\nMonitoramento finalizado.")

