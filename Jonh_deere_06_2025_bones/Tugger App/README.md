# 🚜 Tugger App

This application provides an interface for interacting with the tugger hardware.

## Features

### 🖥️ Graphical User Interface (GUI)
The application features a GUI that allows users to interact with various functions of the tugger hardware.

### 🔑 Employee ID Unlock
Users can unlock the tugger by scanning their employee ID card through the application interface.

### 📷 Rear View Camera System
When the tugger is put into reverse gear, the application automatically launches the system's camera app, effectively providing a rear-view camera function for enhanced safety and visibility.

## Usage

### Prerequisites
Before building the executable, ensure you have Python installed and set up a virtual environment:

1.  **Create a virtual environment:**
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
3.  **Install required libraries:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: You might need to create the `requirements.txt` file first if it doesn't exist, listing all necessary packages.)*

#### Production Build (No Console Window)
```bash
pyinstaller --distpath app --workpath app/build --specpath app/spec --noconsole --name TelemetryAPP main.py
```

#### Test Build (With Console Window)
```bash
pyinstaller --distpath app --workpath app/build --specpath app/spec -F --name TelemetryAPP-CONSOLE main.py
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
1.  The application must be installed in the following directory on the target tugger PCs: `C:\Telemetry\TelmemetryAPP`.
2.  Inside the `C:\Telemetry` directory, create a folder named `images`.
3.  Place all the necessary icon files used by the GUI into this `images` folder.
4. To create the windows task scheduler to execute the code use: `schtasks /create /tn "00 - Telemetry APP" /tr "C:\Telemetry\TelemetryAPP\TelemetryAPP.exe" /sc ONLOGON /RL HIGHEST`
