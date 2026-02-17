from pymodbus.client import ModbusSerialClient

def configure_b22(name, configs):
    client = ModbusSerialClient(port='COM3', baudrate=19200, timeout=1)
    client.connect()

    for reg, val in configs.items():
        result = client.write_register(reg, val, slave=1)
        if result.isError():
            print(f"[{name}] Failed to write {val} to register {reg}")
        else:
            print(f"[{name}] Successfully wrote {val} to register {reg}")


    client.close()

status= {
    40200: 1,
    40300: 1,
    40603: 3
}

banco_banco= {
    40200: 3,  # Pin 4: PNP output pull-down
    40300: 1,  # Pin 2: PNP input
    40603: 4,  # Endereço
}

ct= {
    46103: 2,
}

# Configuração para B22 banco e RPM
configure_b22("B22", configs=banco_banco)
