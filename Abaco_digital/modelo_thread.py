import time
import threading
from pyModbusTCP.client import ModbusClient


valor_lock = threading.Lock()
estado = "a"


def read():
    # init modbus client
    c = ModbusClient("192.168.1.7", port=502, debug=False, auto_open=True)

    global estado, valor_lock

    while True:
        # read 10 registers at address 0, store result in regs list
        lista_registro_1 = c.read_holding_registers(1001, 1)
        lista_registro_2 = c.read_holding_registers(2001, 1)
        lista_registro_3 = c.read_holding_registers(3001, 1)
        lista_registro_4 = c.read_holding_registers(4001, 1)
        # if success display registers

        print(lista_registro_1, lista_registro_2, lista_registro_3, lista_registro_4)
        # sleep 2s before next polling
        time.sleep(.1)


leitor = threading.Thread(target=read(), daemon=True)
leitor.start()
leitor.join()
