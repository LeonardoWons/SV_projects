import pyodbc

from globals\
    import COMPUTER_NAME, DATABASE_URL, VERSION

from handler.handler\
    import exceptionHandler

from _types.types\
    import TelemetryDataType

@exceptionHandler("Error selecting current tugger computer from SQL Server database.")
def selectServerTuggerComputer():
    """
    Retrieves the unique identifier (tugger ID) and equipment type for the current machine from the SQL Server database.

    Returns:
            str | None: The tugger ID as a string if found, otherwise None.
    """
    
    global DATABASE_URL, COMPUTER_NAME

    try:
        connection = pyodbc.connect(DATABASE_URL, autocommit=False, timeout=1)
        cursor = connection.cursor()

        querySelect = f"""
            SELECT DISTINCT ID, EQUIPMENT_TYPE FROM TELEMETRY_Computers 
            WHERE COMPUTER_HOSTNAME = '{COMPUTER_NAME}'
        """

        cursor.execute(querySelect)
        result = cursor.fetchone()

        return result if result else None

    except pyodbc.Error as e:
        print(f"Error selecting server current tugger ID: {e}")

        return None
    
    finally:
        cursor.close()
        connection.close()

@exceptionHandler("Error inserting data into SQL Server database.")
def insertServerTelemetryData(data: TelemetryDataType):
    """
    Insert telemetry data into the SQL Server database.
    
    This function uploads the provided telemetry data to the central SQL Server database. 
    It converts the list of dictionaries into a list of tuples for batch insertion.
    
    Args:
        data (TelemetryDataType): A list of dictionaries containing telemetry data.
            Each dictionary must have the following keys:
            - EQUIPMENT_ID: Unique identifier for the tugger equipment
            - DATE_TIME: Timestamp of the telemetry record in "YYYY-MM-DD HH:MM:SS" format
            - LATITUDE, LONGITUDE, ALTITUDE: GPS position coordinates
            - SIGNAL_QUALITY, SATELLITE_COUNT: GPS signal information
            - PDOP, HDOP, VDOP: GPS precision dilution values
            - SPEED, DIRECTION: Movement speed and direction data
            - PHONIC_WHEEL_RPM: Current rotation per minute from phonic wheel
            - IS_EQUIPMENT_ON, ELECTRIC_CURRENT: Equipment operational status and current
            - IS_INTERNET_CONNECTED, IS_EQUIPMENT_IN_REVERSE: Connection and gear status flags
            - EMPLOYEE_BADGE: Current employee badge ID
            - COMPUTER_HOSTNAME: Hostname of the computer running the telemetry system
            - CODE_VERSION: Software version of the telemetry system
    
    Returns:
        bool: True if data insertion was successful, False otherwise
    """

    global DATABASE_URL, COMPUTER_NAME, VERSION

    try:
        connection = pyodbc.connect(DATABASE_URL, autocommit=False, timeout=1)
        cursor = connection.cursor()
        
        queryInsert = f"""
            INSERT INTO 
                TELEMETRY_Readings(
                    EQUIPMENT_ID,
                    DATE_TIME,

                    LATITUDE,
                    LONGITUDE,
                    ALTITUDE,

                    SIGNAL_QUALITY,
                    SATELLITE_COUNT,

                    PDOP,
                    HDOP,
                    VDOP,

                    SPEED,
                    DIRECTION,
                    
                    PHONIC_WHEEL_RPM,
                    
                    IS_EQUIPMENT_ON,
                    ELECTRIC_CURRENT,

                    IS_INTERNET_CONNECTED,
                    IS_EQUIPMENT_IN_REVERSE,

                    EMPLOYEE_BADGE,
                    COMPUTER_HOSTNAME,
                    CODE_VERSION
                ) 

            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        
        
        #? Convert dictionary list to tuple list
        tupleList = []
        for row in data:
            tupleList.append((
                row['EQUIPMENT_ID'],
                row['DATE_TIME'],

                row['LATITUDE'],
                row['LONGITUDE'],
                row['ALTITUDE'],

                row['SIGNAL_QUALITY'],
                row['SATELLITE_COUNT'],

                row['PDOP'],
                row['HDOP'],
                row['VDOP'],

                row['SPEED'],
                row['DIRECTION'],

                row['PHONIC_WHEEL_RPM'],

                row['IS_EQUIPMENT_ON'],
                row['ELECTRIC_CURRENT'],

                row['IS_INTERNET_CONNECTED'],
                row['IS_EQUIPMENT_IN_REVERSE'],

                row['EMPLOYEE_BADGE'],
                row['COMPUTER_HOSTNAME'],
                row['CODE_VERSION']
            ))

        cursor.fast_executemany = True
        cursor.executemany(queryInsert, tupleList)
        connection.commit()

        return True

    except pyodbc.Error as e:
        print(f"Error inserting server telemetry data: {e}")

        connection.rollback()
        return False
    
    finally:
        cursor.close()
        connection.close()