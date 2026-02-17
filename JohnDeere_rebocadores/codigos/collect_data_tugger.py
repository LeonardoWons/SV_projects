from pymodbus.client import ModbusSerialClient
from struct import unpack as Montafloat


# Slave addresses for GPS and status / Endereços de escravo para GPS e status
slave_gps = 1
slave_current = 2
slave_status = 3

address_status_value = 40001


# Function to collect GPS data / Função para coletar dados de GPS
def get_gps():
    # Create Modbus client / Criar cliente Modbus
    client_gps = ModbusSerialClient(method="rtu", port="COM2", baudrate=19200, timeout=1, parity="N", stopbits=1, bytesize=8)
    client_gps.connect()

    try:
        # Read latitude, longitude, and altitude / Ler latitude, longitude e altitude
        read = client_gps.read_holding_registers(100, 10, slave_gps)
        latitude = Montafloat('!f',
                              bytes.fromhex('{0:04x}'.format(read.registers[0]) + '{0:04x}'.format(read.registers[1])))
        longitude = Montafloat('!f',
                               bytes.fromhex('{0:04x}'.format(read.registers[2]) + '{0:04x}'.format(read.registers[3])))
        altitude = Montafloat('!f',
                              bytes.fromhex('{0:04x}'.format(read.registers[4]) + '{0:04x}'.format(read.registers[5])))
        latitude = str(latitude[0])[:20]
        longitude = str(longitude[0])[:20]
        altitude = str(altitude[0])[:20]

    except Exception as a:
        print(f"Error reading GPS coordinates: {a}")
        # In case of error, return 0 for latitude, longitude, and altitude /
        # Em caso de erro, retornar 0 para latitude, longitude e altitude
        latitude = "NA"
        longitude = "NA"
        altitude = "NA"

    try:
        # Collect signal quality and number of satellites / Coletar qualidade de sinal e número de satélites
        read = client_gps.read_holding_registers(2004, 4, slave_gps)

        signal_quality = Montafloat('!f', bytes.fromhex(
            '{0:04x}'.format(read.registers[0]) + '{0:04x}'.format(read.registers[1])))
        satellite_count = Montafloat('!f', bytes.fromhex(
            '{0:04x}'.format(read.registers[2]) + '{0:04x}'.format(read.registers[3])))
        signal_quality = format(signal_quality[0], '.6f')
        satellite_count = format(satellite_count[0], '.6f')
        signal_quality = signal_quality[:20]
        satellite_count = satellite_count[:20]

    except Exception as b:
        print(f"Error reading signal quality and satellites: {b}")
        # In case of error, return 0 for signal quality and satellite count /
        # Em caso de erro, retornar 0 para qualidade de sinal e número de satélites
        signal_quality = "NA"
        satellite_count = "NA"

    try:
        # Collect PDOP, HDOP, and VDOP values / Coletar valores de PDOP, HDOP e VDOP
        read = client_gps.read_holding_registers(2128, 6, slave_gps)
        pdop = Montafloat('!f',
                          bytes.fromhex('{0:04x}'.format(read.registers[0]) + '{0:04x}'.format(read.registers[1])))
        hdop = Montafloat('!f',
                          bytes.fromhex('{0:04x}'.format(read.registers[2]) + '{0:04x}'.format(read.registers[3])))
        vdop = Montafloat('!f',
                          bytes.fromhex('{0:04x}'.format(read.registers[4]) + '{0:04x}'.format(read.registers[5])))
        pdop = str(pdop[0])[:20]
        hdop = str(hdop[0])[:20]
        vdop = str(vdop[0])[:20]

    except Exception as c:
        print(f"Error reading DOP values: {c}")
        # In case of error, return 0 for PDOP, HDOP, and VDOP / Em caso de erro, retornar 0 para PDOP, HDOP e VDOP
        pdop = "NA"
        hdop = "NA"
        vdop = "NA"

    try:
        # Collect speed and direction / Coletar velocidade e direção
        read = client_gps.read_holding_registers(2206, 4, slave_gps)
        speed = Montafloat('!f', bytes.fromhex('{0:04x}'.format(read.registers[0]) + '{0:02x}'.format(read.registers[1])))
        direction = Montafloat('!f', bytes.fromhex('{0:04x}'.format(read.registers[2]) + '{0:02x}'.format(read.registers[3])))
        speed = str(speed[0])[:20]
        direction = str(direction[0])[:20]

    except Exception as d:
        print(f"Error reading speed and direction: {d}")
        # In case of error, return 0 for speed and direction / Em caso de erro, retornar 0 para velocidade e direção
        speed = "NA"
        direction = "NA"

    client_gps.close()
    # Return all collected GPS data / Retornar todos os dados coletados de GPS
    return [latitude, longitude, altitude, signal_quality, satellite_count, pdop, hdop, vdop, speed, direction]


# Function to get equipment status / Função para coletar o status do equipamento
def get_status():
    # Create Modbus client / Criar cliente Modbus
    clientt = ModbusSerialClient(method="rtu", port="COM2", baudrate=19200, timeout=1, parity="N", stopbits=1, bytesize=8)
    clientt.connect()

    try:
        read_s = clientt.read_holding_registers(address_status_value, 3, slave_status)
        status_chave = str(read_s.registers[0])[:2]
        status_re = str(read_s.registers[1])[:2]

    except Exception as f:
        print(f"Error reading status: {f}")
        status_chave = status_re = "NA"

    clientt.close()

    return [status_chave, status_re]
