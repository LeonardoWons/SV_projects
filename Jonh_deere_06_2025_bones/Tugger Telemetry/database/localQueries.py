import sqlite3 as sql

from globals\
    import LOCAL_TELEMETRY_DB_PATH, LOCAL_TELEMETRY_TABLE,\
           LOCAL_BADGE_DB_PATH, LOCAL_CURRENT_USER_TABLE

from handler.handler\
    import exceptionHandler

from _types.types\
    import TelemetryDataType


#? ---------- Database queries ---------- #?
@exceptionHandler("Error creating local telemetry database or table.")
def configureLocalTelemetryDB():
    """
    Create local telemetry database and table if it doesn't exist.
        
    Returns:
        commit (True | False)
    """
    
    global LOCAL_TELEMETRY_DB_PATH, LOCAL_TELEMETRY_TABLE

    try:
        #? Create table if it doesnt exist
        connection = sql.connect(LOCAL_TELEMETRY_DB_PATH)
        cursor = connection.cursor()

        cursor.execute(f""" 
            CREATE TABLE IF NOT EXISTS {LOCAL_TELEMETRY_TABLE}( 
                ID INTEGER PRIMARY KEY AUTOINCREMENT,

                EQUIPMENT_ID VARCHAR(20),
                EQUIPMENT_TYPE VARCHAR(20),
                DATE_TIME VARCHAR(20),

                LATITUDE VARCHAR(20),
                LONGITUDE VARCHAR(20),
                ALTITUDE VARCHAR(20),

                SIGNAL_QUALITY VARCHAR(20),
                SATELLITE_COUNT VARCHAR(20),

                PDOP VARCHAR(20),
                HDOP VARCHAR(20),
                VDOP VARCHAR(20),

                SPEED VARCHAR(20),
                DIRECTION VARCHAR(20),
                
                PHONIC_WHEEL_RPM VARCHAR(20),

                IS_EQUIPMENT_ON VARCHAR(20),
                ELECTRIC_CURRENT VARCHAR(20),

                IS_INTERNET_CONNECTED VARCHAR(20),
                IS_EQUIPMENT_IN_REVERSE VARCHAR(20),

                EMPLOYEE_BADGE VARCHAR(20),
                COMPUTER_HOSTNAME VARCHAR(20),
                CODE_VERSION VARCHAR(20)
            );
        """)

        connection.commit()
        return True

    except sql.Error as e:
        print(f"Error configuring local telemetry database: {e}")
        
        connection.rollback()
        return False
    
    finally:
        cursor.close()
        connection.close()


#? ---------- Telemetry table queries ---------- #?
@exceptionHandler("Error inserting new rows into local telemetry database.")
def insertLocalTelemetry(data: TelemetryDataType):
    """
    Insert new row into the local telemetry database from a data object.
    
    Args:
        data (TelemetryData): A dictionary containing all telemetry fields.
        
    Returns:
        commit (True | False)
    """

    global LOCAL_TELEMETRY_DB_PATH, LOCAL_TELEMETRY_TABLE

    try:
        connection = sql.connect(LOCAL_TELEMETRY_DB_PATH)
        cursor = connection.cursor()
        
        #? Ensure the order of columns matches the dictionary
        cursor.execute(
            f"""
                INSERT INTO {LOCAL_TELEMETRY_TABLE}(
                    EQUIPMENT_ID,
                    EQUIPMENT_TYPE,
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
            """,
            (
                data["EQUIPMENT_ID"],
                data["EQUIPMENT_TYPE"],
                data["DATE_TIME"],

                data["LATITUDE"],
                data["LONGITUDE"],
                data["ALTITUDE"],

                data["SIGNAL_QUALITY"],
                data["SATELLITE_COUNT"],

                data["PDOP"],
                data["HDOP"],
                data["VDOP"],

                data["SPEED"],
                data["DIRECTION"],

                data["PHONIC_WHEEL_RPM"],

                data["IS_EQUIPMENT_ON"],
                data["ELECTRIC_CURRENT"],
                
                data["IS_INTERNET_CONNECTED"],
                data["IS_EQUIPMENT_IN_REVERSE"],

                data["EMPLOYEE_BADGE"],
                data["COMPUTER_HOSTNAME"],
                data["CODE_VERSION"]
            )
        )
        
        connection.commit()
        return True
    
        
    except sql.Error as e:
        print(f"Error inserting local telemetry data: {e}")

        connection.rollback()
        return False

    finally:
        cursor.close()
        connection.close()
    
@exceptionHandler("Error counting selecting rows from local telemetry database.")
def selectLocalTelemetry(quantity: int = None):
    """
    Select rows from the local telemetry database.
        
    Args:
        quantity (int): quantity of rows to select.    
        
    Returns:
        result (list | None)
    """
    
    global LOCAL_TELEMETRY_DB_PATH, LOCAL_TELEMETRY_TABLE

    try:
        connection = sql.connect(LOCAL_TELEMETRY_DB_PATH)
        connection.row_factory = sql.Row
        cursor = connection.cursor()

        if quantity:
            query = f"""
                SELECT *
                FROM {LOCAL_TELEMETRY_TABLE}
                ORDER BY ID DESC
                LIMIT {quantity};
            """
        else:
            query = f"""
                SELECT *
                FROM {LOCAL_TELEMETRY_TABLE}
                ORDER BY ID;
            """

        cursor.execute(query)
        rows = cursor.fetchall()

        #? Returns the result as a dictionary list
        rowsDict = [dict(row) for row in rows]
        return rowsDict

    except sql.Error as e:
        print(f"Error selecting local telemetry data: {e}")

        connection.rollback()
        return None

    finally:
        cursor.close()
        connection.close()
    
@exceptionHandler("Error deleting rows from local telemetry database.")
def deleteLocalTelemetry(quantity: int = None):
    """
    Delete rows from the local telemetry database.
        
    Args:
        quantity (int): quantity of rows to delete.
        
    Returns:
        commit (True | False)
    """
    
    global LOCAL_TELEMETRY_DB_PATH, LOCAL_TELEMETRY_TABLE

    try:
        connection = sql.connect(LOCAL_TELEMETRY_DB_PATH)
        cursor = connection.cursor()

        if quantity:
            query = f"""
                WITH
                    ListID AS (
                        SELECT ID
                        FROM {LOCAL_TELEMETRY_TABLE}
                        ORDER BY ID
                        LIMIT {quantity}
                    )

                DELETE FROM {LOCAL_TELEMETRY_TABLE} 
                WHERE id IN (ListID);
            """
        else:
            query = f"""
                DELETE FROM {LOCAL_TELEMETRY_TABLE};
            """

        cursor.execute(query)

        connection.commit()
        return True

    except sql.Error as e:
        print(f"Error deleting local telemetry data: {e}")

        connection.rollback()
        return False
    
    finally:
        cursor.close()
        connection.close()


#? ---------- Current user table queries ---------- #?
@exceptionHandler("Error selecting current user from local current user table.")
def selectLocalCurrentUser():
    """
    Clear the current local user table and insert the new current user badge.
    
    Args:
        badge (str): Badge ID of the current employee.
        
    Returns:
        result (list | None)
    """
    
    global LOCAL_BADGE_DB_PATH, LOCAL_CURRENT_USER_TABLE

    connection = sql.connect(LOCAL_BADGE_DB_PATH, autocommit=False)
    cursor = connection.cursor()

    try:
        cursor.execute(f"""
            SELECT *
            FROM {LOCAL_CURRENT_USER_TABLE};
        """)
        currentUser = cursor.fetchone()

        connection.commit()
        return currentUser

    except sql.Error as e:
        print(f"Error selecting local current user: {e}")

        connection.rollback()
        return None

    finally:
        cursor.close()
        connection.close()