import threading
import tkinter as tk

from PIL\
    import Image, ImageTk

from globals\
    import\
        GUI_ROOT, VERSION, PROJECT_PATH, DATA_STORE, DATABASE_URL,\
        GREEN_COLOR, YELLOW_COLOR, BACKGROUND_COLOR,\
        THREAD_LOCK, DEFAULT_DELAY

from handler.handler\
    import exceptionHandler

from util.util\
    import isWifiConnected, readBadgeInput, isValidBadge, setLockValue

from database.localQueries\
    import updateLocalBadges, updateLocalCurrentUser

from database.serverQueries\
    import selectServerBadges


#? ---------- GUI util functions ---------- #?
@exceptionHandler("Error loading image to TKinter app.")
def loadImage(path, size):
    """
    Loads an image, resizes it, and converts it to a Tkinter PhotoImage.

    Args:
        path (str): The file path to the image.
        size (tuple): The desired size (width, height) for the image.

    Returns:
        ImageTk.PhotoImage: The resized image object compatible with Tkinter.
    """

    image = Image.open(path)
    image = image.resize(size, Image.Resampling.LANCZOS)

    return ImageTk.PhotoImage(image)

@exceptionHandler("Error hiding TKinter app.")
def hideGUI():
    """
    Hides the main GUI window.

    Args:
        None

    Returns:
        None
    """

    global GUI_ROOT
    GUI_ROOT.withdraw()

@exceptionHandler("Error showing TKinter app.")
def showGUI():
    """
    Shows the main GUI window.

    Args:
        None

    Returns:
        None
    """

    global GUI_ROOT
    GUI_ROOT.deiconify()


#? ---------- GUI actions ---------- #?
@exceptionHandler("Error updating local badges database.")
def updateBadges():
    """
    Updates the local badges database by fetching data from the server.
    Disables the update button during the process and provides user feedback.

    Args:
        None

    Returns:
        bool: True if the update was successful, False otherwise.
    """

    global GUI_ROOT, DATABASE_URL, BACKGROUND_COLOR

    GUI_ROOT.btnUpdateLocalBadgesDB.configure(state="disabled", bg=BACKGROUND_COLOR) 
    
    try:
        if not isWifiConnected():
            GUI_ROOT.lblButtonAction.configure(text="Erro ao conectar a rede Wi-Fi", fg="red")
            return False
        
        badges = selectServerBadges(DATABASE_URL) # Fetch from SQL Server
        updateLocalBadges(badges) # Insert into local SQLite DB
                
        GUI_ROOT.lblButtonAction.configure(text="Atualizado com sucesso", fg=GREEN_COLOR)
        return True
    
    except:
        GUI_ROOT.lblButtonAction.configure(text="Erro ao atualizar dados", fg="red")

    finally:
        GUI_ROOT.btnUpdateLocalBadgesDB.configure(state="normal", bg=YELLOW_COLOR)
        GUI_ROOT.after(DEFAULT_DELAY, lambda: GUI_ROOT.lblButtonAction.configure(text=""))

@exceptionHandler("Thread error reading badge event.")
def threadReadBadgeEvent():
    """
    Handles the badge reading event in a separate thread.
    Reads badge input, validates it, and updates the GUI accordingly.
    Unlocks the tugger if conditions are met.

    Args:
        None

    Returns:
        None
    """

    global\
        GUI_ROOT, DATA_STORE, THREAD_LOCK
    
    GUI_ROOT.after(0, GUI_ROOT.btnToggleBadgeRead.configure(state="disabled", bg=BACKGROUND_COLOR))

    currentBadge = ""
    badgeRead = ""
    isReadingOK = False
    isBadgeOK = False

    try:
        #? Read badge input from keyboard
        badgeRead = readBadgeInput() 

        if not badgeRead:
            GUI_ROOT.lblButtonAction.configure(text="Leitura vazia", fg="red")
            isReadingOK = False
            return
        
        currentBadge = badgeRead
        GUI_ROOT.after(0, lambda: GUI_ROOT.lblButtonAction.configure(text="Crachá lido", fg=GREEN_COLOR))

        isBadgeOK = isValidBadge(currentBadge)

        if not isBadgeOK:
            GUI_ROOT.after(1000, lambda: GUI_ROOT.lblButtonAction.configure(text="Crachá inválido", fg="red"))
            isReadingOK = False
            return
        
        if not DATA_STORE.get("isKeyON"): 
            GUI_ROOT.after(1000, lambda: GUI_ROOT.lblButtonAction.configure(text="Primeiro, ligue o equipamento.", fg="red"))
        else: 
            GUI_ROOT.after(1000, lambda: GUI_ROOT.lblButtonAction.configure(text="Acesso liberado", fg=GREEN_COLOR))

        isReadingOK = True

    except:
        isReadingOK = False
        GUI_ROOT.after(1000, lambda: GUI_ROOT.lblButtonAction.configure(text="Erro ao ler crachá", fg="red"))

    finally:
        currentBadge = currentBadge if isBadgeOK else "unknown"

        updateLocalCurrentUser(currentBadge)
        DATA_STORE.set("currentBadge", currentBadge)
        DATA_STORE.set("isReadingBadge", False)

        GUI_ROOT.after(0, lambda: GUI_ROOT.btnToggleBadgeRead.configure(state="normal", bg=GREEN_COLOR))
        GUI_ROOT.after(DEFAULT_DELAY, lambda: GUI_ROOT.lblButtonAction.configure(text=""))

        #? Update values if tugger should be unlocked
        if not isReadingOK: return
        if not DATA_STORE.get("isKeyON"): return
        if DATA_STORE.get("isTuggerUnlocked"): return

        #? Unlock tugger
        isSetLockValueOK = setLockValue(1)
        if not isSetLockValueOK:
            GUI_ROOT.after(1000, lambda: GUI_ROOT.lblButtonAction.configure(text="Erro ao desbloquear rebocador", fg="red"))
            return

        #? If lock value was changed, hide
        DATA_STORE.set("isTuggerUnlocked", True)
        GUI_ROOT.after(0, lambda: hideGUI())

@exceptionHandler("Error updating GUI while reading badge")
def toggleBadgeRead():
    """
    Toggles the badge reading process.
    Starts a new thread to read the badge if not already reading.
    Provides user feedback on the GUI.

    Args:
        None

    Returns:
        bool: True if the badge reading thread was started successfully, False otherwise.
    """

    global GUI_ROOT, DATA_STORE
    
    if DATA_STORE.get("isReadingBadge"): return False
    DATA_STORE.set("isReadingBadge", True)

    GUI_ROOT.lblButtonAction.configure(text="Lendo crachá...", fg=GREEN_COLOR)

    try:
        badgeReadThread = threading.Thread(target=threadReadBadgeEvent, daemon=True)
        badgeReadThread.start()
        return True

    except:
        GUI_ROOT.lblButtonAction.configure(text="Erro criando thread de leitura", fg="red")
        DATA_STORE.set("isReadingBadge", False)
        return False


#? ---------- Create GUI ---------- #?
@exceptionHandler("Error creating TKinter loading screen")
def createLoader():
    """
    Creates a loading screen for the Tugger Telemetry application.
    Displays a message indicating that the app is loading.

    Args:
        None

    Returns:
        None
    """

    global GUI_ROOT, BACKGROUND_COLOR, GREEN_COLOR, VERSION

    #? App configuration
    GUI_ROOT.title("Tugger Telemetry")
    GUI_ROOT.attributes("-fullscreen", True)
    GUI_ROOT.protocol("WM_DELETE_WINDOW", lambda: hideGUI())  # Hide Windows close button
    GUI_ROOT.wm_attributes("-topmost", True)  # Keep window on top
    
    #? Set window and sizes
    windowHeight = GUI_ROOT.winfo_screenheight()
    fontSize = round(windowHeight * 0.03)
    imgSize = round((windowHeight / 7) * 2)

    #? Load images
    iconJD = loadImage(rf"{PROJECT_PATH}\images\johnDeere.png", (imgSize, imgSize))
    GUI_ROOT.iconJD = iconJD

    #? JohnDeere logo
    lblJohnDeereLogo = tk.Label(
        GUI_ROOT,
        image=iconJD,
        bg=BACKGROUND_COLOR
    )
    lblJohnDeereLogo.place(
        relx=0.5,
        rely=0.35,
        anchor=tk.CENTER
    )

    #? Main label
    lblLoading = tk.Label(
        GUI_ROOT,
        text="Inicializando aplicação...",
        font=("Helvetica", fontSize, "bold"),
        bg=BACKGROUND_COLOR,
        fg=GREEN_COLOR
    )
    lblLoading.place(
        relx=0.5,
        rely=0.5,
        anchor=tk.CENTER
    )
    GUI_ROOT.lblLoading = lblLoading
    
    #? Version label
    lblVersion = tk.Label(
        GUI_ROOT,
        text=f"Telemetry v{VERSION}",
        font=("Helvetica", int(fontSize // 2.5)),
        bg=BACKGROUND_COLOR,
        fg="grey"
    )
    lblVersion.place(
        relx=0.98,
        rely=0.98,
        anchor=tk.SE
    )

    GUI_ROOT.update_idletasks()
    GUI_ROOT.update()

@exceptionHandler("Error creating TKinter app")
def createGUI():
    """
    Creates and initializes the main GUI for the Tugger Telemetry application.
    Sets up the window, loads images, and places all UI elements.

    Args:
        None

    Returns:
        None
    """
    
    global\
        GUI_ROOT, VERSION, PROJECT_PATH, THREAD_LOCK,\
        GREEN_COLOR, YELLOW_COLOR, BACKGROUND_COLOR

    #? Clear any previous widgets
    for widget in GUI_ROOT.winfo_children(): widget.destroy()

    #? Set window and font size
    windowWidth = GUI_ROOT.winfo_screenwidth()
    windowHeight = GUI_ROOT.winfo_screenheight()
    fontSize = round(windowHeight * 0.03)


    #? Set app frame
    frame = tk.Frame(GUI_ROOT)
    frame.pack()

    #? Set app canvas
    canvas = tk.Canvas(
        frame,
        width=windowWidth,
        height=windowHeight,
        bd=0,
        highlightthickness=0,
        bg=BACKGROUND_COLOR
    )
    canvas.pack()


    #? Load images
    gridScreenSize = round(windowHeight / 7)
    imgBadgeSize   = round((windowHeight / 7) * 2)
    
    imgHeader = loadImage(rf"{PROJECT_PATH}\images\header.png",      (windowWidth, gridScreenSize))
    iconSV    = loadImage(rf"{PROJECT_PATH}\images\sensorVille.png", (gridScreenSize, gridScreenSize))
    imgBadge  = loadImage(rf"{PROJECT_PATH}\images\badgeReader.png", (imgBadgeSize, imgBadgeSize))

    GUI_ROOT.imgHeader  = imgHeader
    GUI_ROOT.iconSV = iconSV
    GUI_ROOT.imgBadge = imgBadge


    #? Header
    canvas.create_image(0, 0, image=imgHeader, anchor="nw")
    canvas.create_image(windowWidth - (windowHeight * 0.15) // 2, 0, image=iconSV, anchor="n")


    #? Main label
    lblBadge = tk.Label(
        GUI_ROOT,
        text="Ligue o equipamento, depois passe o crachá no local identificado pela imagem abaixo para habilitar o equipamento",
        font=("Helvetica", fontSize),
        bg=BACKGROUND_COLOR,
        fg="black",
        wraplength=(windowWidth // 10) * 9
    )
    lblBadge.place(
        relx=0.5,
        y=gridScreenSize * 2.25,
        anchor=tk.CENTER
    )
    GUI_ROOT.lblBadge = lblBadge


    #? Main badge image
    canvas.create_image(
        windowWidth / 2,
        gridScreenSize * 4,
        image=imgBadge,
        anchor=tk.CENTER
    )


    #? Display results label
    lblButtonAction = tk.Label(
        GUI_ROOT,
        text="",
        font=("Helvetica", int(fontSize // 1.5)),
        bg=BACKGROUND_COLOR,
        fg=GREEN_COLOR
    )
    lblButtonAction.place(
        relx=0.5,
        y=gridScreenSize * 1.3,
        anchor=tk.CENTER
    )
    GUI_ROOT.lblButtonAction = lblButtonAction


    #? Refresh database button
    btnUpdateLocalBadgesDB = tk.Button(
        GUI_ROOT,
        text="Atualizar dados",
        font=("Helvetica", int(fontSize // 1.5)),
        bg=YELLOW_COLOR,
        command=lambda: updateBadges()
    )
    btnUpdateLocalBadgesDB.place(
        relx=0.9,
        y=gridScreenSize * 1.35,
        anchor=tk.CENTER
    )
    GUI_ROOT.btnUpdateLocalBadgesDB = btnUpdateLocalBadgesDB


    #? Toggle badge read button
    btnToggleBadgeRead = tk.Button(
        GUI_ROOT,
        text="Habilitar crachá",
        font=("Helvetica", int(fontSize // 1.2)),
        bg=GREEN_COLOR,
        fg="white",
        command=lambda: toggleBadgeRead()
    )
    btnToggleBadgeRead.place(
        relx=0.5,
        y=gridScreenSize * 5.5 + gridScreenSize / 2,
        anchor=tk.CENTER
    )
    GUI_ROOT.btnToggleBadgeRead = btnToggleBadgeRead


    #? Version label
    lblVersion = tk.Label(
        GUI_ROOT,
        text=f"Telemetry v{VERSION}",
        font=("Helvetica", int(fontSize // 2.5)),
        bg=BACKGROUND_COLOR,
        fg="gray"
    )
    lblVersion.place(
        relx=0.98,
        rely=0.98,
        anchor=tk.SE
    )
    GUI_ROOT.lblVersion = lblVersion


    #? Run app
    GUI_ROOT.after(0, lambda: showGUI())