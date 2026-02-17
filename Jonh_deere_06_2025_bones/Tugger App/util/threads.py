import time
import subprocess

import psutil
import pygetwindow as gw

from globals\
    import GUI_ROOT, DATA_STORE, THREAD_INTERVAL, THREAD_LOCK

from handler.handler\
    import exceptionHandler

from util.util\
    import getLatestData, setLockValue, hideTitleBar


#? ---------- Background thread for checking tugger key value ---------- #?
@exceptionHandler(
    "Thread error checking tugger key value.",
    retry=True,
    retryAttempts="infinite",
    retryDelay=THREAD_INTERVAL
)
def threadCheckTuggerKey():
    """
    Monitor the tugger lock status and update the GUI accordingly.

    This function runs in a continuous loop, checking the tugger's key value
    using the `getLatestData` function. If the key status indicates the tugger
    should be locked (value 0), it updates the global `isTuggerUnlocked` variable and
    triggers the GUI to display the lock status.

    Notes:
        - The function uses a thread lock (`THREAD_LOCK`) to ensure thread-safe
          access to shared resources.
        - The loop includes a 1-second delay between iterations to reduce CPU usage.

    Exceptions:
        - Any exceptions encountered during execution are logged, and the loop
          continues execution.
    """
    
    from gui.gui import showGUI
    global THREAD_INTERVAL, GUI_ROOT, DATA_STORE, THREAD_LOCK

    while True:
        try:
            #? Get latest data if telemetry API is available
            with THREAD_LOCK: latestData = getLatestData()
            if latestData is None: continue

            #? Get lock value if telemetry API is available
            with THREAD_LOCK: keyValue = latestData.get("IS_EQUIPMENT_ON")
            if keyValue is None: continue

            #? Update global variable only if value changed
            if DATA_STORE.get("isKeyON") == keyValue: continue
            DATA_STORE.set("isKeyON", False if keyValue != "1" else True)

            #? If key is OFF lock tuger 
            if DATA_STORE.get("isKeyON"): continue
            isSetLockValueOK = setLockValue(0)

            #? If lock value was changed, show GUI
            if not isSetLockValueOK: continue
            DATA_STORE.set("isTuggerUnlocked", False)
            GUI_ROOT.after(0, lambda: showGUI())

        except Exception as e:
            print(f"Error in threadCheckTuggerLock: {e}")
        
        finally:
            #? Ensure the thread sleeps for the specified interval
            time.sleep(THREAD_INTERVAL)


#? ---------- Background thread for checking tugger camera usage ---------- #?
@exceptionHandler(
    "Thread error checking camera usage.",
    retry=True,
    retryAttempts="infinite",
    retryDelay=THREAD_INTERVAL
)
def threadCheckCameraUsage():
    """
    Monitor the rear camera usage and manage the camera application state.

    This function runs in a continuous loop, checking the rear camera status
    using the `getLatestData` function. Based on the status, it either launches
    or terminates the Windows Camera application. The function also ensures the
    camera window is maximized when opened.

    Notes:
        - The function uses a thread lock (`THREAD_LOCK`) to ensure thread-safe
          access to shared resources.
        - The loop includes a 1-second delay between iterations to reduce CPU usage.

    Exceptions:
        - Any exceptions encountered during execution are logged, and the loop
          continues execution.
    """
    
    global THREAD_INTERVAL, GUI_ROOT, DATA_STORE
    
    cameraWindowNames = ["Câmera", "Camera"]
    cameraWindow = None

    while True:
        try:
            #? Check if camera app is running
            isCameraAppRunning = any(
                proc.info['name'] == 'WindowsCamera.exe'\
                for proc in psutil.process_iter([ 'name' ])
            )

            #? If camera app isnt running, start process
            if not isCameraAppRunning:
                cameraWindow = None
                subprocess.Popen(
                    "explorer shell:appsfolder\\Microsoft.WindowsCamera_8wekyb3d8bbwe!App",
                    shell=True
                )
                continue

            #? If camera app is running and camera window is not set
            if not cameraWindow:
                while not cameraWindow: 
                    for windowName in cameraWindowNames:
                        window = gw.getWindowsWithTitle(windowName)
                        if not window: continue

                        cameraWindow = window[0]
                        break

                    time.sleep(1)

                cameraWindow.minimize()
                hideTitleBar(cameraWindow)

            #? Variable to check if camera window is active
            isWindowOpened = cameraWindow.isMaximized

            #? If tugger is blocked and camera is open, close camera
            if not DATA_STORE.get("isTuggerUnlocked") and isWindowOpened:
                cameraWindow.minimize()
                DATA_STORE.set("isCameraOpened", False)
                continue

            #? Get latest data if telemetry API is available
            with THREAD_LOCK: latestData = getLatestData()
            if latestData is None: continue

            #? Get rear value if telemetry API is available
            with THREAD_LOCK: rearValue = latestData.get("IS_EQUIPMENT_IN_REVERSE")
            if rearValue is None: continue

            #? Convert rear value to boolean
            with THREAD_LOCK: isTuggerInReverse = True if rearValue == "1" else False

            #? If tugger on reverse gear and camera not opened
            if isTuggerInReverse and not isWindowOpened:
                cameraWindow.restore()
                cameraWindow.activate()
                cameraWindow.maximize()

                DATA_STORE.set("isCameraOpened", True)
                continue

            #? If tugger not on reverse gear and camera opened
            if not isTuggerInReverse and isWindowOpened:
                time.sleep(10)

                cameraWindow.minimize()
                DATA_STORE.set("isCameraOpened", False)
                continue

        except Exception as e:
            print(f"Error in threadCheckCameraUsage: {e}")
        
        finally:
            #? Ensure the thread sleeps for the specified interval
            time.sleep(THREAD_INTERVAL)