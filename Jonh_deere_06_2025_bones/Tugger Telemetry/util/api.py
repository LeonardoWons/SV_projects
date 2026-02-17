import json
import asyncio
import requests
import websockets

from globals\
    import SAVE_INTERVAL, TELEMETRY_API_URL

from handler.handler\
    import exceptionHandler


#? ---------- Keep connection (Ping-pong) ---------- #?
@exceptionHandler("API Websocket error sending ping message to server.")
async def sendPing(websocket):
    """
    Periodically sends ping messages to maintain the WebSocket connection.
    
    This function runs an infinite loop that sends a "ping" message to the server
    every 30 seconds. It helps keep the WebSocket connection alive and detect
    disconnections.
    
    The function implements an exponential backoff strategy for error handling:
    - On success: Uses a normal 30-second interval between pings
    - On error: Waits for a delay that doubles after each consecutive failure
                (starting at 3 seconds, capped at 60 seconds)
    - After recovery: Resets to the initial retry delay (3 seconds)
    
    Args:
        websocket: The WebSocket connection object to send pings through.
        
    Returns:
        None: This function runs indefinitely until an exception occurs.
        
    Note:
        The function will continue running despite errors, implementing
        exponential backoff to avoid overwhelming the server during outages.
    """

    normalInterval = 30
    retryDelay = 3
    maxRetryDelay = 60
    
    while True:
        try:
            await websocket.send("ping")
            await asyncio.sleep(normalInterval)

            retryDelay = 3 # Reset retry delay after success run
            
        except Exception as e:
            print(f"API Error sending ping: {e}")
            
            await asyncio.sleep(retryDelay)
            retryDelay = min(retryDelay * 2, maxRetryDelay) # Increase retry delay on each error

@exceptionHandler("API Websocket error recieving/reading pong message from server.")
async def listenPong(websocket):
    """
    Listens for pong responses from the server to verify connection status.
    
    This function runs an infinite loop that waits for messages from the server.
    It specifically looks for "pong" responses, which indicate the server is 
    still connected and responding to ping messages.
    
    The function implements an exponential backoff strategy for error handling:
    - On success: Immediately waits for the next message
    - On error: Waits for a delay that doubles after each consecutive failure
                (starting at 3 seconds, capped at 60 seconds)
    - After recovery: Resets to the initial retry delay (3 seconds)
    
    Args:
        websocket: The WebSocket connection object to listen on.
        
    Returns:
        None: This function runs indefinitely until an exception occurs.
        
    Note:
        The function will continue running despite errors, implementing
        exponential backoff to avoid overwhelming the server during outages.
        Messages other than "pong" are ignored.
    """

    retryDelay = 3
    maxRetryDelay = 60

    while True:
        try:
            message = await websocket.recv()
            if message != "pong": continue

            retryDelay = 3 # Reset retry delay after success run
                
        except Exception as e:
            print(f"API Error recieving pong: {e}")
            
            await asyncio.sleep(retryDelay)
            retryDelay = min(retryDelay * 2, maxRetryDelay) # Increase retry delay on each error


#? ---------- Send telemetry data to servers ---------- #?
@exceptionHandler("API Websocket error sending telemetry data to server.")
async def sendTelemetryData(websocket):
    """
    Sends telemetry data to the server via WebSocket connection.
    
    This function runs an infinite loop that:
    1. Retrieves the latest telemetry data from the local database
    2. Formats the data for transmission (simplified to include key GPS values)
    3. Sends the data to the server as a JSON string
    
    The function implements an exponential backoff strategy for error handling:
    - On success: Uses a normal 3-second interval between data transmissions
    - On error: Waits for a delay that doubles after each consecutive failure
                (starting at 6 seconds, capped at 60 seconds)
    - After recovery: Resets to the initial retry delay (6 seconds)
    - If no data is available: Waits for the normal interval before trying again
    
    Args:
        websocket: The WebSocket connection object to send data through.
        
    Returns:
        None: This function runs indefinitely until an exception occurs.
        
    Note:
        The function will continue running despite errors, implementing
        exponential backoff to avoid overwhelming the server during outages.
    """

    normalInterval = 1
    retryDelay = 6
    maxRetryDelay = 60

    while True:
        try:
            response = requests.get(TELEMETRY_API_URL)

            if response.status_code != 200: 
                await asyncio.sleep(normalInterval)
                continue

            data = response.json()[0]

            if ("message" in data) or (data is None): 
                await asyncio.sleep(normalInterval)
                continue

            formattedData = {
                "tugger_id":      data["EQUIPMENT_ID"],
                "equipment_type": data["EQUIPMENT_TYPE"],
                "latitude" :      data["LATITUDE"],
                "longitude":      data["LONGITUDE"],
                "plant":          "CQ01"
            }

            await websocket.send( json.dumps(formattedData) )

            retryDelay = 6 # Reset retry delay after success run
            await asyncio.sleep(normalInterval)

        except Exception as e:
            print(f"API Error sending data to server: {e}")

            await asyncio.sleep(retryDelay)
            retryDelay = min(retryDelay * 2, maxRetryDelay) # Increase retry delay on each error

@exceptionHandler("API Websocket error connecting to server {serverURL}.")
async def connectServer(serverURL):
    """
    Establish and manage a WebSocket connection to a remote server.
    
    This function creates a persistent WebSocket connection to the specified server,
    then manages three concurrent tasks:
    1. Sending periodic ping messages to maintain the connection
    2. Listening for pong responses to confirm server availability
    3. Continuously sending telemetry data to the server
    
    The function implements a robust task management approach:
    - It uses asyncio.wait() to monitor all tasks
    - If any task completes or raises an exception, all other tasks are canceled
    - Task exceptions are re-raised to allow proper error handling by the caller
    
    Args:
        serverURL (str): The WebSocket URL of the server to connect to
                        (format: "wss://hostname/path")
    
    Raises:
        ConnectionError: If the WebSocket connection cannot be established
        WebSocketException: For WebSocket protocol-related errors
        Exception: For any error that occurs in the background tasks
    
    Note:
        This function is designed to run indefinitely until a task fails.
        When an exception occurs, the exception handler will log the error
        and the caller is expected to implement a reconnection strategy.
    """
    
    while True:
        try:
            async with websockets.connect(serverURL) as websocket:
                #? Keep connection (Ping-pong)
                taskSendPing   = asyncio.create_task( sendPing(websocket) )
                taskListenPong = asyncio.create_task( listenPong(websocket) )

                #? Send telemetry data
                taskSendData   = asyncio.create_task( sendTelemetryData(websocket) )

                #? This will wait until any task completes or raises an exception
                done, pending = await asyncio.wait(
                    [taskSendPing, taskListenPong, taskSendData],
                    return_when = asyncio.FIRST_COMPLETED
                )
                
                #? Clean up any pending tasks
                for task in pending: task.cancel()
                
                #? Check if any task completed with an exception
                for task in done: task.result()
        
        except Exception as e:
            print(f"API Error connecting to server {serverURL}: {e}")
            
        finally:
            #? Wait before attempting to reconnect
            await asyncio.sleep(SAVE_INTERVAL)

@exceptionHandler("API Websocket error connecting to servers {serverURls}.")
async def connectServers(*serverURLs):
    """
    Connect to multiple servers concurrently with automatic reconnection.
    
    Args:
        *serverURLs: Variable number of server URLs to connect to
        
    Example:
        await connectServer(JDUBER_DEV_WS_URL, JDUBER_PROD_WS_URL)
        await connectServer(JDUBER_PROD_WS_URL)  # Single server
    """
    
    if not serverURLs:
        print("No server URLs provided")
        return
    
    #? Create connection tasks for each server
    tasks = [
        asyncio.create_task(connectServer(url)) 
        for url in serverURLs
    ]
    
    #? Run all connections concurrently
    await asyncio.gather(*tasks, return_exceptions=True)