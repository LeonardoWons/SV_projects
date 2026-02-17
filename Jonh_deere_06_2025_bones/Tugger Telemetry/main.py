import threading
from contextlib import asynccontextmanager
from pickle import GLOBAL

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from serial.rfc2217 import COM_PORT_OPTION

from globals import DATA_STORE, THREAD_LOCK, VERSION

from util.util import initModbusClient, ensureModbusConnection, setLockValue, isWifiConnected

from util.threads import threadSaveTelemetryData, threadWebsocketAPI

from database.localQueries import configureLocalTelemetryDB

from database.serverQueries import selectServerTuggerComputer

from _models.models import LockRequestModel


#? -------------------- Startup event handler for FastAPI -------------------- ?#
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Asynchronous context manager for FastAPI application lifecycle events.

    This function is used by FastAPI to manage setup and teardown operations
    during the application's lifespan. Code before the `yield` statement
    is executed on application startup, and code after `yield` is executed
    on application shutdown.

    On startup, this function sets the `SERVER_READY` event from the `globals`
    module, signaling that the FastAPI application is initialized and ready
    to handle requests. This is useful for coordinating with other background
    threads or services that depend on the API being active.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    
    from globals import SERVER_READY
    SERVER_READY.set()
    
    #? The application runs here
    yield  
    
    #? Shutdown logic (runs when application is shutting down)
    pass


#? -------------------- Intialize FastAPI app -------------------- ?#
app = FastAPI(
    title="Tugger Telemetry Service", 
    description="Combined telemetry data collection and API service.",
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


#? -------------------- FastAPI endpoints -------------------- ?#
@app.get("/health")
def healthCheck():
    """
    Health check endpoint for service monitoring.
    
    This can be used by monitoring tools or other 
    services to confirm the API is operational.
    
    Returns:
        dict: A dictionary with basic service information:
            - status (str): Service status, "online" when the service is running correctly
            - version (str): Current software version number from VERSION constant
    
    Example:
        GET /health
        Response: {"status": "online", "version": "1.2.3"}
    """

    global VERSION

    return { "status": "online", "version": VERSION }

@app.get("/api/telemetryData")
def telemetryGET():
    """
    Retrieve the latest tugger telemetry data.
    
    This endpoint provides access to the most recent telemetry record stored in the local database.
    The data includes sensor readings, GPS coordinates, operational statistics, 
    connection status, and metadata about the tugger.
    
    Returns:
        dict: A dictionary containing the latest telemetry data with the following keys:
            - EQUIPMENT_ID (str): Unique identifier for the tugger equipment.
            - EQUIPMENT_TYPE (str): Type of the equipment (e.g., "Tugger", "Forklift").
            - DATE_TIME (str): Timestamp of the telemetry data in "YYYY-MM-DD HH:MM:SS" format.
            - LATITUDE (str): GPS latitude coordinate.
            - LONGITUDE (str): GPS longitude coordinate.
            - ALTITUDE (str): GPS altitude coordinate.
            - SIGNAL_QUALITY (str): Signal quality of the GPS.
            - SATELLITE_COUNT (str): Number of satellites connected to the GPS.
            - PDOP (str): Position Dilution of Precision (PDOP) value.
            - HDOP (str): Horizontal Dilution of Precision (HDOP) value.
            - VDOP (str): Vertical Dilution of Precision (VDOP) value.
            - SPEED (str): Current speed of the tugger.
            - PHONIC_WHEEL_RPM (str): Current rotation per minute from phonic wheel
            - DIRECTION (str): Direction of the tugger's movement.
            - IS_EQUIPMENT_ON (str): Status indicating if the equipment is turned on.
            - ELECTRIC_CURRENT (str): Current electrical current value.
            - IS_INTERNET_CONNECTED (str): "1" if the tugger is online, "0" if offline.
            - IS_EQUIPMENT_IN_REVERSE (str): Status indicating if the equipment is in reverse gear.
            - EMPLOYEE_BADGE (str): Current employee badge ID or "0" if none assigned.
            - COMPUTER_HOSTNAME (str): Hostname of the computer running the telemetry system.
            - CODE_VERSION (str): Software version of the telemetry system.
    
    Example:
        GET /api/telemetry
    """
    
    global DATA_STORE

    currentData = DATA_STORE.get("latestData")

    if not currentData:
        return { "message": "No telemetry data available yet." }
    
    return currentData

@app.post("/api/lockRequest")
def lockPOST(request: LockRequestModel):
    """
    Control the tugger's physical locking mechanism.
    
    This endpoint sends commands to the tugger's hardware through the Modbus connection
    to either lock or unlock the device. It ensures thread-safe access to the
    shared Modbus client and validates the hardware response.
    
    Args:
        request (ModelLockRequest): The request object containing:
            - unlock (bool): True to unlock the tugger, False to lock it
    
    Returns:
        dict: A response indicating success and the new lock status:
            - success (bool): Always True if no exception is raised
            - status (str): "unlocked" or "locked" reflecting the new state
    
    Raises:
        HTTPException(503): If unable to connect to the tugger hardware
        HTTPException(500): If the hardware command fails to execute
    
    Example:
        POST /api/lockRequest
        Body: {"unlock": true}
    """

    global DATA_STORE, THREAD_LOCK

    client = ensureModbusConnection(DATA_STORE.get("client"))
    if DATA_STORE.get("client") != client: DATA_STORE.set("client", client)

    if not client:
        raise HTTPException(status_code=503, detail="Unable to connect to tugger hardware.")
    
    #? Convert boolean to integer (0=locked, 1=unlocked)
    lockValue = 1 if request.unlock else 0
    
    #? Set the tugger locker mode
    with THREAD_LOCK: isResponseOK = setLockValue(client, lockValue)
    if not isResponseOK: raise HTTPException(status_code=500, detail="Failed to set tugger locker status.")
    
    return { "success": True, "status": "unlocked" if request.unlock else "locked" }


#? -------------------- Set initial values, threads and FastAPI server -------------------- ?#
def main():
    """
    Main function to initialize the Tugger Telemetry Service.
    This function sets up the FastAPI application, initializes global variables,
    starts background threads for telemetry data saving and WebSocket communication,
    and runs the FastAPI server.

    Returns:
        None: This function does not return any value. It starts the FastAPI server
              and runs indefinitely until interrupted.
    """
    #? Initialize global thread variables
    DATA_STORE.set("client", initModbusClient())
    DATA_STORE.set("latestData", None)

    #? Set global computer data variables
    computerData = selectServerTuggerComputer()
    DATA_STORE.set("equipmentID", computerData[0] if isWifiConnected() else "0")
    DATA_STORE.set("equipmentType", computerData[1] if computerData else "unknown")

    #? Create local bage database and table if it doesn't exist
    configureLocalTelemetryDB()

    #? Create thread responsible for saving the telemetry data
    saveTelemetryDataThread = threading.Thread(
        target=threadSaveTelemetryData,
        daemon=True
    )
    saveTelemetryDataThread.start()

    #? Create thread for sending telemetry data to JDUber backend
    websocketAPIThread = threading.Thread(
        target=threadWebsocketAPI,
        daemon=True
    )
    websocketAPIThread.start()

    #? Start FastAPI server
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=5000, 
        log_level="error", 
        access_log=False,
        log_config={
            "version": 1,
            "disable_existing_loggers": True,
            "formatters": {},
            "handlers": {"default": {"class": "logging.NullHandler"}},
            "loggers": {"uvicorn": {"handlers": ["default"], "level": "CRITICAL"}},
        }
    )

if __name__ == "__main__": main()