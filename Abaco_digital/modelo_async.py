import asyncio
import time
import threading
from pyModbusTCP.client import ModbusClient


async def read():
    # init modbus client
    c = ModbusClient("192.168.1.7", port=502, debug=False, auto_open=True)

    while True:
        # read 10 registers at address 0, store result in regs list
        regs_l = c.read_holding_registers(1001, 10)

        # if success display registers
        if regs_l:
            print('reg ad #0 to 9: %s' % regs_l)
        else:
            print('unable to read registers')

        # sleep 2s before next polling
        time.sleep(.1)


leitor = threading.Thread(target=asyncio.run(read(), debug=True), daemon=True)
leitor.start()
leitor.join()

