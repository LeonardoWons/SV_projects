import time
import threading
from pyModbusTCP.client import ModbusClient


valor_lock = threading.Lock()
estado = "a"
counter1 = 0


def read():
    # init modbus client
    c = ModbusClient("192.168.1.7", port=502, debug=False, auto_open=True)

    global estado, valor_lock, counter1


    while True:
        # read 10 registers at address 0, store result in regs list
        lista_registro_1 = c.read_holding_registers(1000, 1)
        lista_registro_2 = c.read_holding_registers(2001, 1)
        #lista_registro_3 = c.read_holding_registers(3001, 1)
        #lista_registro_4 = c.read_holding_registers(4001, 1)
        # if success display registers

        if lista_registro_1[0] == 84:
            counter1 += 1

        print(lista_registro_1, counter1)
        # sleep 2s before next polling


leitor = threading.Thread(target=read(), daemon=True)
leitor.start()
leitor.join()
