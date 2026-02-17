# 🛰️ Tugger Telemetry

This application runs in the background on tugger PCs. It collects telemetry data from tugger hardware, provides an API for data access and control, stores data locally, and synchronizes it with a central SQL Server database and a WebSocket-based backend.

## Features

### 📊 Enhanced Data Collection & API
*   **Modbus Data Acquisition**: Gathers various telemetry data points from tugger hardware via Modbus:
    *   GPS Coordinates (Latitude, Longitude, Altitude)
    *   GPS Signal Quality & Satellite Count
    *   GPS Precision Data (PDOP, HDOP, VDOP)
    *   Movement Data (Speed, Direction)
    *   Equipment Status (e.g., Lock Status, Reverse Gear Status)
    *   Current User Badge ID
*   **FastAPI Endpoints**: Exposes a local HTTP API for interaction and data retrieval:

    | Method | Endpoint          | Description                                                 |
    |--------|-------------------|-------------------------------------------------------------|
    | GET    | `/health`         | Checks the operational status and version of the service.   |
    | GET    | `/api/telemetryData` | Retrieves the latest collected telemetry data.              |
    | POST   | `/api/lockRequest`  | Allows remote control of the tugger's locking mechanism.    |

*   **Real-time WebSocket Communication**: Sends telemetry data to a central backend (JDUber) via WebSocket for real-time monitoring.

### 💾 Robust Local Storage
*   Utilizes a local SQLite database (`localTelemetryDB.db`) to temporarily store collected telemetry data.
*   Manages user badge information in a separate local SQLite database (`localBadgesDB.db`).
*   This ensures data integrity and continued operation even if network connectivity to central systems is temporarily lost.

### ☁️ Centralized Server Synchronization
*   Periodically connects to a central SQL Server database (`CQ_LOGISTIC_PROJECTS` on `cq-logistic-projects-prod-cq-db.jdnet.deere.com`).
*   Uploads all locally stored telemetry data from `localTelemetryDB.db` to the central server.

### 🗑️ Automated Data Purging
*   Once telemetry data is successfully uploaded to the SQL Server, the corresponding records are deleted from the local SQLite database (`localTelemetryDB.db`) to conserve disk space.

### ⚙️ Background Operation & Resilience
*   Designed to run continuously as a background console application.
*   Includes error handling and reconnection logic for Modbus, SQL Server, and WebSocket communications.
*   Uses a thread-safe data store for managing shared application state.

## Usage

### Prerequisites
Before building the executable, ensure you have Python installed and set up a virtual environment:

1.  **Create a virtual environment (e.g., `.venv`):**
    ```bash
    python -m venv .venv
    ```
2.  **Activate the virtual environment:**
    *   On Windows:
        ```bash
        .\.venv\Scripts\activate
        ```
    *   On macOS/Linux:
        ```bash
        source .venv/bin/activate
        ```
3.  **Install required libraries from `requirements.txt`:**
    ```bash
    pip install -r requirements.txt
    ```

### Configuration
Key configuration parameters are managed in `globals.py`, including:
*   Database connection strings (SQL Server, WebSocket URLs)
*   Local database paths and names
*   Modbus slave IDs
*   Service version (`VERSION = 4.2`)

The application expects to be installed in `C:\Telemetry`, as defined by `PROJECT_PATH` in `globals.py`.

### Testing the WebSocket API
The project includes an `index.html` file. You can open this file in a web browser to test and visualize the data being transmitted over the WebSocket API in real-time. This is useful for development and debugging purposes.

### Building the Executable
To generate the executable files for deployment, navigate to the project's root directory (`Tugger Telemetry`) in your terminal and run one of the following commands:

#### Production Build (No Console Window)
```bash
pyinstaller --distpath app --workpath app/build --specpath app/spec --noconsole --name TelemetrySERVICE main.py
```

#### Test Build (With Console Window)
```bash
pyinstaller --distpath app --workpath app/build --specpath app/spec -F --name TelemetrySERVICE-CONSOLE main.py
```

These commands use PyInstaller to package the application (`main.py`) into executable files located in the `app` directory.

**Command Options:**
*   `--distpath app`: Specifies the output directory for the final executable.
*   `--workpath app/build`: Specifies the directory for temporary build files.
*   `--specpath app/spec`: Specifies the directory for the `.spec` file.
*   `--noconsole`: Prevents the console window from appearing (production build only).
*   `-F`: Creates a one-file bundled executable (test build only).
*   `--name`: Sets the name of the executable and spec file.

### Installation on Tugger PCs
1.  The application and its associated `localTelemetryDB.db` (and `localBadgesDB.db` if used by this version) are expected to be in the following directory on the target tugger PCs: `C:\Telemetry\TelemetrySERVICE`. This path is configured in `globals.py`.
2.  To create the windows task scheduler to execute the code use: `schtasks /create /tn "00 - Telemetry SERVICE" /tr "C:\Telemetry\TelemetrySERVICE\TelemetrySERVICE.exe" /sc ONLOGON /RL HIGHEST`