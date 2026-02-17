import time
import asyncio
from datetime import datetime, timedelta

from globals\
    import SERVER_READY, DATA_STORE, THREAD_LOCK,\
           COMPUTER_NAME, VERSION, SAVE_INTERVAL,\
           JDUBER_DEV_WS_URL, JDUBER_PROD_WS_URL

from handler.handler\
    import exceptionHandler


from util.util\
    import ensureModbusConnection, isWifiConnected, getAllData

from util.api\
    import connectServers

from database.localQueries\
    import selectLocalCurrentUser, insertLocalTelemetry, selectLocalTelemetry, deleteLocalTelemetry

from database.serverQueries\
    import selectServerTuggerComputer, insertServerTelemetryData


#? ---------- Background thread for saving telemetry data ---------- #?
@exceptionHandler(
    "Thread error saving telemetry data to local database.",
    retry=True,
    retryAttempts="infinite",
    retryDelay=SAVE_INTERVAL
)
def threadSaveTelemetryData():
    """
    Background thread function for collecting and managing telemetry data.
    
    This function runs as a daemon thread and performs the following operations in a continuous loop:
    1. Retrieves the tugger ID from the server if not already available
    2. Checks if the user badge data is current (less than 9 hours old)
    3. Ensures the Modbus client connection is active
    4. Collects telemetry data from the tugger device
    5. Adds metadata (tugger ID, timestamp, connection status, etc.)
    6. Saves telemetry data to the local database
    7. If internet connection is available, transmits all locally stored data to the central server
    8. Deletes local data after successful transmission to the server
    
    The function uses thread locking to ensure database operations are thread-safe.
    It sleeps for the duration specified by SAVE_INTERVAL between iterations.
    
    Returns:
        None: This function runs indefinitely until the program terminates.
    """
    
    global THREAD_LOCK, COMPUTER_NAME, SAVE_INTERVAL

    while True:
        try:
            #? Wait for server to be ready
            if not SERVER_READY.is_set(): continue

            #? Get time dependant data
            currentDatetime = datetime.now()
            userBadgeData = selectLocalCurrentUser()
            userBadgeDatetime = datetime.strptime(userBadgeData[2], "%Y-%m-%d %H:%M:%S")

            #? Only save telemetry data if the user badge is updated
            if (currentDatetime - userBadgeDatetime) > timedelta(hours=9): continue

            #? Test Wi-Fi connection
            isWifiOK = isWifiConnected()

            #? If code started but couldn't get computer data, try to fecth again from SQL Server
            equipmentID = DATA_STORE.get("equipmentID")
            equipmentType = DATA_STORE.get("equipmentType")

            if (equipmentID == "0" or equipmentType == "unknown") and isWifiOK:
                computerData = selectServerTuggerComputer()
                equipmentID = computerData[0] if computerData else "0"
                DATA_STORE.set("equipmentID", equipmentID)

                equipmentType = computerData[1] if computerData else "unknown"
                DATA_STORE.set("equipmentType", equipmentType)

            #? Ensure Modbus client is connected
            client = ensureModbusConnection(DATA_STORE.get("client"))
            if DATA_STORE.get("client") != client: DATA_STORE.set("client", client)
            if not client: continue

            #? Get telemetry data from tugger devices
            telemetryData = getAllData(client)

            #? Add additional telemetry data
            telemetryData["EQUIPMENT_ID"] = equipmentID
            telemetryData["EQUIPMENT_TYPE"] = equipmentType
            telemetryData["DATE_TIME"] = currentDatetime.strftime("%Y-%m-%d %H:%M:%S")
            telemetryData["IS_INTERNET_CONNECTED"] = "1" if isWifiOK else "0"
            telemetryData["CODE_VERSION"] = VERSION
            telemetryData["COMPUTER_HOSTNAME"] = COMPUTER_NAME
            telemetryData["EMPLOYEE_BADGE"] = userBadgeData[1] if userBadgeData[1] else "0"

            #? Always save telemetry data locally first
            with THREAD_LOCK: insertLocalTelemetry(telemetryData)

            #? Select local telemetry data if there is a connection to SQL Server
            if not isWifiOK: continue
            with THREAD_LOCK: allLocalData = selectLocalTelemetry()

            #? If there is no local data, skip to next iteration
            if not allLocalData: continue

            #? Select latest telemetry data
            latestData = selectLocalTelemetry(1)

            #? Only update latest data if its a new value
            if latestData != DATA_STORE.get("latestData"): DATA_STORE.set("latestData", latestData)

            #? Send all new data to SQL Server
            with THREAD_LOCK: isServerDataSent = insertServerTelemetryData(allLocalData)

            #? Delete local telemetry data if it was sent to SQL Server
            if not isServerDataSent: continue
            with THREAD_LOCK: deleteLocalTelemetry()

        except Exception as e:
            print(f"Error in threadSaveTelemetryData: {e}")
        
        finally:
            #? Ensure the thread sleeps for the specified interval
            time.sleep(SAVE_INTERVAL)


#? ---------- Background thread for saving latest data into endpoint ---------- #?
@exceptionHandler(
    "API Thread error creating websocket connections to server.",
    retry=True,
    retryAttempts="infinite",
    retryDelay=SAVE_INTERVAL
)
def threadWebsocketAPI():
    """
    Maintains a persistent WebSocket connection to the JDUber backend server.
    
    This function runs as an asynchronous background task that:
    1. Establishes a WebSocket connection to the JDUber development server
    2. Manages the connection through the connectServer function, which handles:
    - Regular ping/pong health checks
    - Sending telemetry data to the remote server
    3. Automatically attempts to reconnect if the connection is lost
    
    The function implements a simple reconnection strategy:
    - If the connection fails for any reason, wait 2 seconds
    - Then attempt to reconnect to the server
    - Repeat indefinitely to ensure persistent communication
    
    Returns:
        None: This function runs indefinitely until the program terminates.
    
    Note:
        This function should be run in an asyncio event loop or as a Task.
        The reconnection logic ensures the system can recover from network
        interruptions without requiring manual intervention.
    """
    
    async def webscoketAPI():
        global JDUBER_DEV_WS_URL, JDUBER_PROD_WS_URL

        while True:
            try:
                #? Wait for server to be ready
                if not SERVER_READY.is_set():
                    await asyncio.sleep(1)
                    continue

                #? Connect to servers and run all tasks
                await connectServers(JDUBER_DEV_WS_URL, JDUBER_PROD_WS_URL)

            except Exception as e:
                print(f"API Error in threadWebsocketAPI: {e}")

            finally:
                #? Wait before trying to reconnect
                await asyncio.sleep(SAVE_INTERVAL)

    asyncio.run( webscoketAPI() )