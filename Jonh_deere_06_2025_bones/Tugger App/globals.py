import threading
import tkinter as tk

from _stores.stores\
    import DataStore

#? Current code version
VERSION = "4.5"


#? Project base folder path
PROJECT_PATH = r"C:\Telemetry"


#? John Deere default colors
GREEN_COLOR  = "#367C2B"
YELLOW_COLOR = "#FFDE00"
BACKGROUND_COLOR = "#F2F2F2"


#? Local and temporary database files
LOCAL_BADGE_DB = "localBadgesDB.db"
LOCAL_BADGE_DB_PATH = rf"{PROJECT_PATH}\{LOCAL_BADGE_DB}"

LOCAL_BADGE_TABLE = "localBadgesTable"
LOCAL_CURRENT_USER_TABLE = "localCurrentUserTable"


#? Localhost URL adresses
LOCAL_HOST_URL = "http://127.0.0.1:5000"
TELEMETRY_API_URL = f"{LOCAL_HOST_URL}/api/telemetryData"
LOCK_API_URL = f"{LOCAL_HOST_URL}/api/lockRequest"


#? SQL Server database connection URL
DATABASE_URL = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=cq-logistic-projects-prod-cq-db.jdnet.deere.com,1434;"
    "Database=CQ_LOGISTIC_PROJECTS;"
    "UID=ACQ0225;"
    "PWD=fZhJQYO1t!;"
)


#? GUI default settings
GUI_ROOT = tk.Tk()
DEFAULT_DELAY = 3000


#? Data Store for global data variables
DATA_STORE = DataStore.getInstance()


#? Thread variables
THREAD_INTERVAL = 1
THREAD_LOCK = threading.Lock()