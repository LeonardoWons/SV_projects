import re
import keyboard
import requests
import subprocess

import win32gui
import win32con

from globals\
    import LOCK_API_URL, TELEMETRY_API_URL

from handler.handler\
    import exceptionHandler

from database.localQueries\
    import selectLocalBadge


#? ---------- General functions ---------- #?
@exceptionHandler("Error hiding window title bar.")
def hideTitleBar(window):
    """
    Hides the title bar of a given window by modifying its style.

    Args:
        window (object): The window object whose title bar is to be hidden.

    Returns:
        None: This function does not return any value. It modifies the window style directly.
    """
    
    hwnd = window._hWnd
    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    style &= ~win32con.WS_CAPTION
    
    win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
    win32gui.SetWindowPos(
        hwnd, None, 0, 0, 0, 0,
        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED
    )

@exceptionHandler("Error testing connection to Wi-Fi.", errorReturn=False)
def isWifiConnected(ssid="3apt1s"):
    """
    Check if the device is connected to a specific WiFi network.
    
    Args:
        ssid (str): The name of the WiFi network to check for
        
    Returns:
        bool: True if connected to the specified network, False otherwise
    """

        #? Get network interfaces information
    output = subprocess.check_output(
        "netsh wlan show interfaces", 
        shell=True
    ).decode('cp1252', errors='replace') 
    
    if ssid.lower() not in output.lower(): return False 
    
    return True


#? ---------- Tugger registers handling ---------- #?
@exceptionHandler("Error changing tugger lock value.", errorReturn=False)
def setLockValue(lockValue: int):
    """
    Sets the tugger lock state by sending a request to the lock control API.
    
    This function sends a POST request to the lock API endpoint to change the 
    tugger's lock state. It implements a retry mechanism with exponential backoff
    to handle temporary network issues or service unavailability.
    
    Args:
        lockValue (int): The lock state to set:
            - 0: Lock the tugger (secure state)
            - 1: Unlock the tugger (operational state)
    
    Returns:
        bool: True if the lock state was successfully changed (received HTTP 200),
              False if all retry attempts failed.
              
    Note:
        This function will attempt up to 10 retries with increasing delays between
        attempts if the API call fails or returns a non-200 status code.
    """

    global LOCK_API_URL

    try:
        response = requests.post(
            LOCK_API_URL,
            json={ "unlock": True if lockValue else False },
            timeout=1
        )

        if response.status_code != 200: return False
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"--- Request error retrieving latest data: \n{e}")
        return None
    
    except Exception as e:
        print(f"--- Error setting lock value: \n{e}")
        return False

@exceptionHandler("Error retrieving tugger data from registers.", errorReturn=None)
def getLatestData():
    """
    Retrieve the latest telemetry data from the telemetry API.

    This function communicates with the telemetry API using a GET request to 
    fetch the latest telemetry data. It expects the API to return a JSON list,
    and it will return the first object from that list.

    Returns:
        dict: A dictionary containing the first telemetry data object from the API 
              response, or None if the request fails, the response is not 200,
              the response is not valid JSON, or the JSON data is empty.
    """

    global TELEMETRY_API_URL

    try:
        response = requests.get(TELEMETRY_API_URL, timeout=1)
        if response.status_code != 200: return None

        data = response.json()
        if not data: return None

        return data[0]
    
    except requests.exceptions.RequestException as e:
        print(f"--- Request error retrieving latest data: \n{e}")
        return None
    
    except Exception as e:
        print(f"--- Error retrieving latest data: \n{e}")
        return None
        

#? ---------- Empolyee Badge functions ---------- #?
@exceptionHandler("Error reading keyboard input.", errorReturn=False)
def readBadgeInput():
    """
    Reads keyboard input events until 'Enter' is pressed, simulating a badge reader.

    This function blocks execution while recording keyboard events. It filters
    out key releases, the 'Enter' and 'Shift' keys, and any key events not
    representing a single character.

    The collected characters are then formatted by:
    1. Removing all non-alphanumeric characters.
    2. Converting the result to uppercase.
    3. Removing a leading '0' if present.

    Returns:
        str: The formatted badge string read from the keyboard input, or an
             empty string if no valid characters were read before 'Enter'.
    """
        
    badgeRead = ""
    events = keyboard.record(until="enter")

    #? Process recorded events
    for event in events:
        if event.event_type != keyboard.KEY_DOWN: continue
        if event.name == "enter" or event.name == "shift": continue
        if len(event.name) != 1: continue

        badgeRead += event.name

    formattedBadge = re.sub(r"[^a-zA-Z0-9]", "", badgeRead).upper()
    if formattedBadge[0] == "0": formattedBadge = formattedBadge[1:]

    return formattedBadge

@exceptionHandler("Error validating badge.", errorReturn=False)
def isValidBadge(badge: str):
    """
    Checks if the provided badge string exists in the local badge database.

    Args:
        badge (str): The badge identifier string to validate. Note that this
                     function expects the badge string to be already cleaned
                     (e.g., special characters removed, correct case) if necessary
                     before being passed to this function.

    Returns:
        bool: True if the badge is found in the local database (via searchLocalBadge),
              False otherwise or if an error occurs during the database search.
    """

    isValidBadge = selectLocalBadge(badge)
    if not isValidBadge: return False

    return True