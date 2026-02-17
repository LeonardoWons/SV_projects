import subprocess
from struct\
    import unpack as Montafloat

from pymodbus.client\
    import ModbusSerialClient

from globals\
    import SLAVE_GPS, SLAVE_STATUS, SLAVE_CLIENT, COM_PORT

from handler.handler\
    import exceptionHandler


#? ---------- General functions ---------- #?
@exceptionHandler("Error initializing eternal Modbus client.")
def initModbusClient(port: str = COM_PORT, timeout:float = 1):
    """
    Initialize a persistent Modbus serial client connection.
    
    Creates and establishes a connection to a Modbus device over a serial port.
    This function should be called once at application startup to create the
    client that will be used throughout the application lifecycle.
    
    Args:
        port (str): Serial port name to connect to (e.g., "COM2" on Windows).
                    Defaults to "COM2".
        timeout (float): Connection timeout in seconds. Defaults to 1 second.
    
    Returns:
        client (ModbusSerialClient | None)
            
    Note:
        The client is configured with 3 retries by default. For reconnection 
        handling, see the ensureModbusConnection function.
    """

    client = ModbusSerialClient(
        port=port,
        timeout=timeout,
        retries=3
    )
    
    if not client.connect(): return None
    return client

@exceptionHandler("Error ensuring Modbus connection.")
def ensureModbusConnection(client: ModbusSerialClient | None, port: str = COM_PORT, timeout:float = 1):
    """
    Ensures the Modbus client is connected and available for communication.
    
    This function handles three possible states:
    1. No client exists (client is None): Creates a new client using initModbusClient()
    2. Client exists but is disconnected: Attempts to reconnect the existing client
    3. Client exists and is already connected: Returns the client unchanged
    
    Args:
        client (ModbusSerialClient | None): An existing Modbus client instance or None
                                           if no client has been created yet.
        port (str): Serial port name to connect to if a new client needs to be created.
                   Defaults to "COM2".
        timeout (float): Connection timeout in seconds for a new client.
                        Defaults to 1 second.
    
    Returns:
        ModbusSerialClient: A connected Modbus client instance.
        None: If client creation or connection failed.
    """
    
    if client is None: 
        return initModbusClient(port=port, timeout=timeout)

    if not client.is_socket_open(): 
        client.connect()
        return client
        
    return client
                
@exceptionHandler("Error testing connection to Wi-Fi.", errorReturn=False)
def isWifiConnected(ssid="3apt1s"):
    """
    Check if the device is connected to a specific WiFi network.
    
    Args:
        ssid (str): The name of the WiFi network to check for
        
    Returns:
        bool: True if connected to the specified network, False otherwise
    """

        #? Get network interfaces information
    output = subprocess.check_output(
        "netsh wlan show interfaces", 
        shell=True
    ).decode('cp1252', errors='replace') 
    
    if ssid.lower() not in output.lower(): return False 
    
    return True


#? ---------- Tugger registers handling ---------- #?
@exceptionHandler("Error reading tugger register.")
def readRegister(client: ModbusSerialClient, address: int, count: int, slave: int):
    """
    Reads holding registers from a Modbus device.

    Attempts to read a specified number of holding registers starting from a given
    address on a specific slave device using the provided Modbus client.

    Args:
        client (ModbusSerialClient): An initialized and connected ModbusSerialClient instance.
        address (int): The starting address of the registers to read.
        count (int): The number of registers to read.
        slave (int): The Modbus slave ID to target.

    Returns:
        list[int] | None: A list containing the integer values read from the registers,or None if a communication error occurs or the Modbus device
        returns an error response.
    """

    response = client.read_holding_registers(
        address=address,
        count=count,
        slave=slave
    )

    if response.isError(): return None
    
    return response.registers

@exceptionHandler("Error formatting GPS register data.", errorReturn="0")
def formatRegister(registers: list, startIndex: int):
    """
    Helper function to format data from tugger registers.

    Args:
        registers (list): List of register values.
        startIndex (int): Starting index for the registers to be formatted.

    Returns:
        str: Formatted data as a string.
    """
    
    formattedData = Montafloat(
        '!f',
        bytes.fromhex(
            '{0:04x}'.format(registers[startIndex]) + '{0:04x}'.format(registers[startIndex + 1])
        )
    )
    
    formattedData = str(formattedData[0])[:20]
    return formattedData

@exceptionHandler("Error setting tugger lock value.", errorReturn=False)
def setLockValue(client: ModbusSerialClient, blockValue: int):
    """
    Sets the lock/unlock state of the tugger's physical mechanism via Modbus.

    This function sends a command to the Modbus slave device (identified by `SLAVE_CLIENT`
    from globals) to control its locking mechanism. It writes to a specific register
    (address 40400) to set the desired state.

    Args:
        client (ModbusSerialClient): An initialized and connected ModbusSerialClient instance.
        blockValue (int): The value to write to the register, representing the lock state.
                          Typically, 0 for locked and 1 for unlocked (or vice-versa,
                          depending on hardware implementation).

    Returns:
        bool: True if the Modbus write operation was initiated successfully (does not
              guarantee the physical lock changed, only that the command was sent).
              Returns False if the `exceptionHandler` catches an error and is configured
              to return False.
    """

    global SLAVE_CLIENT

    client.write_register(
        address=40400,
        value=blockValue,
        slave=SLAVE_CLIENT
    )

    return True


#? ---------- Get tugger registers data ---------- #?
@exceptionHandler("Error retrieving GPS data from tugger registers.")
def getGPSData(client: ModbusSerialClient):
    """
    Collects and formats various GPS-related data points from the tugger via Modbus.

    This function reads multiple sets of registers from the Modbus slave device
    (identified by `SLAVE_GPS` from globals) to retrieve raw GPS data.
    It then uses the `formatRegister` helper function to convert these raw values
    into human-readable string representations for:
    - Coordinates: Latitude, Longitude, Altitude
    - Signal Information: Signal Quality, Satellite Count
    - Precision Metrics: PDOP, HDOP, VDOP (Dilution of Precision)
    - Motion Data: Speed, Direction

    Args:
        client (ModbusSerialClient): An initialized and connected ModbusSerialClient instance.

    Returns:
        list[str]: A list of strings containing the formatted GPS data in the following order:
                   [latitude, longitude, altitude, signalQuality, satelliteCount,
                    pdop, hdop, vdop, speed, direction].
                   If an error occurs during Modbus reading at the `readRegister` level
                   and it returns None, subsequent `formatRegister` calls might receive None,
                   leading to "0" in the output list for those fields due to its own
                   `exceptionHandler` configuration.

    See Also:
        readRegister: Function used to read raw data from Modbus registers.
        formatRegister: Helper function to format raw register data.
    """
    
    global SLAVE_GPS

    #? Read tugger data from registers
    coordenates = readRegister(client, 100, 10, SLAVE_GPS) # 101
    signal      = readRegister(client, 2004, 4, SLAVE_GPS) # 2005
    precision   = readRegister(client, 2128, 6, SLAVE_GPS) # 2129
    motion      = readRegister(client, 2206, 4, SLAVE_GPS) # 2207
    

    #? Format latitude, longitude, and altitude
    latitude  = formatRegister(coordenates, 0)
    longitude = formatRegister(coordenates, 2)
    altitude  = formatRegister(coordenates, 4)
    
    
    #? Format signal quality and number of satellites
    signalQuality   = formatRegister(signal, 0)
    sattelliteCount = formatRegister(signal, 2)


    #? Format PDOP, HDOP, VDOP
    #* PDOP (Position Dilution of Precision):
    # - Overall accuracy of 3D position (horizontal + vertical)
    # - Combines HDOP and VDOP
    pdop = formatRegister(precision, 0)
    
    #* HDOP (Horizontal Dilution of Precision):
    # - Accuracy of horizontal position (latitude, longitude)
    # - Affects horizontal accuracy
    hdop = formatRegister(precision, 2)
    
    #* VDOP (Vertical Dilution of Precision):
    # - Accuracy of vertical position (altitude)
    # - Affects vertical accuracy
    vdop = formatRegister(precision, 4)


    #? Format speed and direction
    speed     = formatRegister(motion, 0)
    direction = formatRegister(motion, 2)
    
    
    #? Return all collected GPS data
    return [
        latitude,
        longitude,
        altitude,

        signalQuality,
        sattelliteCount,

        pdop,
        hdop,
        vdop,

        speed,
        direction
    ]

@exceptionHandler("Error retrieving equipment status from tugger registers.", errorReturn=["0", "0"])
def getStatusData(client: ModbusSerialClient):
    """
    Collects the key status and rear status from the tugger via Modbus.

    This function reads specific registers from the Modbus slave device
    (identified by `SLAVE_STATUS` from globals) to determine the current
    status of the key and rear sensors/status.

    The raw register values are converted to strings, and only the first
    two characters are taken to represent the status (e.g., "0" or "1").

    The `exceptionHandler` decorator manages potential errors during Modbus
    communication. If an error occurs, it's configured to return `["0", "0"]`
    as a default/error state.

    Args:
        client (ModbusSerialClient): An initialized and connected ModbusSerialClient instance.

    Returns:
        list[str]: A list containing two string elements:
                   - `keyStatus` (str): The status of the tugger's key.
                   - `rearStatus` (str): The status of the tugger's rear mechanism/sensor.
                   Returns `["0", "0"]` if an error is handled by the decorator.

    Globals Used:
        SLAVE_STATUS (int): The Modbus slave ID for the status module on the tugger.

    See Also:
        readRegister: Function used to read raw data from Modbus registers.
    """
    
    global SLAVE_STATUS

    #? Read tugger data from registers
    status = readRegister(client, 40001, 3, slave=SLAVE_STATUS)
        
    keyStatus  = str(status[0])[:2]
    rearStatus = str(status[1])[:2]

    return [
        keyStatus,
        rearStatus
    ]


@exceptionHandler("Error retrieving equipment RPM from tugger registers.", errorReturn="0")
def getRpmData(client: ModbusSerialClient):
    """
        Collects the counts per minute via Modbus.

        This function reads specific registers from the Modbus slave device
        (identified by `SLAVE_CLIENT` from globals) to determine the current
        RPM from the phonic wheel.

        The raw register values are converted to RPM by performing a mathematical
        calculation: dividing the number of counted pulses by the number of teeth
        on the phonic wheel, resulting in the number of revolutions per minute.

        The `exceptionHandler` decorator manages potential errors during Modbus
        communication. If an error occurs, it is configured to return "0" as a
        default/error state.

        Args:
            client (ModbusSerialClient): An initialized and connected ModbusSerialClient instance.

        Returns:
            str: A string containing the calculated RPM value.

                  Returns "0" if an error is handled by the decorator.

        Globals Used:
            SLAVE_CLIENT (int): The Modbus slave ID for the RPM module on the tugger.
            NUMBER_OF_THEETH (int): Number of teeth on the phonic wheel.

        See Also:
            readRegister: Function used to read raw data from Modbus registers.
    """

    global SLAVE_CLIENT
    global NUMBER_OF_THEETH

    #? Read tugger data from registers
    cpm = readRegister(client, 40020, 1, slave=SLAVE_CLIENT)

    rpm = cpm[0] / NUMBER_OF_THEETH

    return str(rpm)


@exceptionHandler("Error transforming tugger data into dictionary.")
def getAllData(client: ModbusSerialClient):
    """
    Aggregates all collected GPS and status data from the tugger into a single dictionary.

    This function serves as a high-level data collection utility. It calls:
    - `getGPSData()` to retrieve detailed GPS information.
    - `getStatusData()` to retrieve lock and rear status information.
    - `getRpmData()` to retrieve rpm of phonic wheel.

    It then combines these data points into a structured dictionary with well-defined keys,
    making the data easily accessible and ready for further processing, storage, or transmission.
    A placeholder for `ELECTRIC_CURRENT` is included, which is noted as "not_get".

    Args:
        client (ModbusSerialClient): An initialized and connected ModbusSerialClient instance,
                                     which will be passed to `getGPSData`, `getStatusData` and `getRpmData`.

    Returns:
        dict[str, str]: A dictionary where keys are descriptive names for data points
                        (e.g., "LATITUDE", "IS_EQUIPMENT_ON") and values are their
                        corresponding string representations. The specific keys are:
                        "LATITUDE", "LONGITUDE", "ALTITUDE",
                        "SIGNAL_QUALITY", "SATELLITE_COUNT", "PDOP",
                        "HDOP", "VDOP", "SPEED", "DIRECTION",
                        "PHONIC_WHEEL_RPM", "IS_EQUIPMENT_ON",
                        "ELECTRIC_CURRENT", "IS_EQUIPMENT_IN_REVERSE".
                        If underlying functions return error values (e.g., "0"), those
                        will be present in the dictionary.

    See Also:
        getGPSData: Function to collect GPS data.
        getStatusData: Function to collect equipment status data.
        getRpmData: Function to collect RPM data.
    """

    gps = getGPSData(client)
    status = getStatusData(client)
    rpm = getRpmData(client)

    #? Data dictionary to store all values
    return {
        "LATITUDE": gps[0],
        "LONGITUDE": gps[1],
        "ALTITUDE": gps[2],

        "SIGNAL_QUALITY": gps[3],
        "SATELLITE_COUNT": gps[4],

        "PDOP": gps[5],
        "HDOP": gps[6],
        "VDOP": gps[7],

        "SPEED": gps[8],
        "DIRECTION": gps[9],

        "PHONIC_WHEEL_RPM": rpm,

        "IS_EQUIPMENT_ON": status[0],
        "ELECTRIC_CURRENT": "not_get", # Placeholder for current value

        "IS_EQUIPMENT_IN_REVERSE": status[1],
    }