import socket
import threading

from _stores.stores\
    import DataStore

#? Current code version
VERSION = "4.5.1"


#? Computer host name
COMPUTER_NAME = socket.gethostname()


#? Project base folder path
PROJECT_PATH = r"C:\Telemetry"


#? Local and temporary database files
LOCAL_TELEMETRY_DB = "localTelemetryDB.db"
LOCAL_TELEMETRY_DB_PATH = rf"{PROJECT_PATH}\{LOCAL_TELEMETRY_DB}"
LOCAL_TELEMETRY_TABLE = "localTelemetryTable"

LOCAL_BADGE_DB = "localBadgesDB.db"
LOCAL_BADGE_DB_PATH = rf"{PROJECT_PATH}\{LOCAL_BADGE_DB}"
LOCAL_CURRENT_USER_TABLE = "localCurrentUserTable"


#? Localhost URL adresses
LOCAL_HOST_URL = "http://127.0.0.1:5000"
TELEMETRY_API_URL = f"{LOCAL_HOST_URL}/api/telemetryData"
LOCK_API_URL = f"{LOCAL_HOST_URL}/api/lockRequest"


#? JDUber server URL adresses
JDUBER_DEV_WS_URL = "wss://jduberbackend-dev.jdnet.deere.com/ws/tuggers_on_time"
JDUBER_PROD_WS_URL = "wss://jduberbackend.deere.com/ws/tuggers_on_time"


#? SQL Server database connection URL
DATABASE_URL = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=cq-logistic-projects-prod-cq-db.jdnet.deere.com,1434;"
    "Database=CQ_LOGISTIC_PROJECTS;"
    "UID=ACQ0225;"
    "PWD=fZhJQYO1t!;"
)


#? Slave address for tugger hardware access
SLAVE_GPS     = 1
SLAVE_CURRENT = 2
SLAVE_STATUS  = 3 # B22 A - Pin 4: Key Status & Pin 2: Rear Status
SLAVE_CLIENT  = 4 # B22 B - Pin 4: Block Tugger & Pin 2: Count Per Minute (CPM)


#? Variables for telemetry data collection
DATA_STORE = DataStore.getInstance()
SERVER_READY = threading.Event()
THREAD_LOCK = threading.Lock()
SAVE_INTERVAL = 1  # second
NUMBER_OF_THEETH = 4
COM_PORT = "COM11"
