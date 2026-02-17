import threading

from globals import GUI_ROOT

def startMainApp():
    """
    Initializes the main application by performing various setup tasks in a separate thread.
    
    Returns:
        None: This function does not return any value. It performs setup tasks and switches
              to the main application GUI.
    """

    global GUI_ROOT

    #? Update loading screen label
    GUI_ROOT.lblLoading.configure(text="Inicializando variáveis globais...")

    #? Initialize global data variables
    from globals import DATA_STORE
    DATA_STORE.set("currentBadge", "unknown")
    DATA_STORE.set("isReadingBadge", False)
    DATA_STORE.set("isCameraOpened", False)
    DATA_STORE.set("isKeyON", False)

    #? Update loading screen label
    GUI_ROOT.lblLoading.configure(text="Bloqueando rebocador...")

    #? Set initial tugger hardware lock as 0 (locked)
    from util.util import setLockValue
    import time
    while not setLockValue(0): time.sleep(1)
    DATA_STORE.set("isTuggerUnlocked", False)

    #? Update loading screen label
    GUI_ROOT.lblLoading.configure(text="Configurando banco de dados local...")

    #? Create local bage database and table if it doesn't exist
    from database.localQueries import configureLocalBadgesDB
    configureLocalBadgesDB()

    #? Update loading screen label
    GUI_ROOT.lblLoading.configure(text="Atualizando banco de dados local...")

    #? Update local badge database with server data
    from util.util import isWifiConnected
    if isWifiConnected():
        from database.serverQueries import selectServerBadges
        from globals import DATABASE_URL
        badges = selectServerBadges(DATABASE_URL)

        from database.localQueries import updateLocalBadges
        updateLocalBadges(badges)

    #? Update loading screen label
    GUI_ROOT.lblLoading.configure(text="Inicializando thread de verificação da chave...")

    #? Create thread responsible for checking the tugger key value
    from util.threads import threadCheckTuggerKey
    checkTuggerKeyThread = threading.Thread(
        target=threadCheckTuggerKey,
        daemon=True
    )
    checkTuggerKeyThread.start()

    #? Update loading screen label
    GUI_ROOT.lblLoading.configure(text="Inicializando thread de verificação da câmera...")

    #? Create thread responsible for checking the camera usage
    from util.threads import threadCheckCameraUsage
    checkCameraUsageThread = threading.Thread(
        target=threadCheckCameraUsage,
        daemon=True
    )
    checkCameraUsageThread.start()

    #? Switches from loading screen to main application GUI
    from gui.gui import createGUI
    createGUI()

    GUI_ROOT.after(0, lambda: createGUI())

def threadStartMainApp():
    """
    Starts the main app tasks in a separate thread to avoid blocking the GUI.
    
    Returns:
        None: This function does not return any value. It starts the main application
              setup in a separate thread.
    """

    startMainAppThread = threading.Thread(
        target=startMainApp,
        daemon=True
    )
    startMainAppThread.start()

def main():
    """
    Main function to start the application. This function initializes the GUI, sets up the loading screen,
    and starts the main application tasks in a separate thread.
    
    Returns:
        None: This function does not return any value. It initializes the GUI and starts
              the main application tasks in a separate thread.
    """

    #?Start app as loding screen
    from gui.gui import createLoader
    createLoader()

    #? Start main application tasks in a separate thread
    from globals import GUI_ROOT
    GUI_ROOT.after(1000, threadStartMainApp)

    #? Start the GUI main loop
    GUI_ROOT.mainloop()

if __name__ == "__main__": main()