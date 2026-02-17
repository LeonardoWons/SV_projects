import inspect
import traceback
import linecache
from tkinter import messagebox
from typing import Literal

def getParamsDict(function, args, kwargs):
    """
    Get a dictionary mapping parameter names to their values.

    Args:
        function (Callable): The function whose parameters are being mapped.
        args (tuple): Positional arguments passed to the function.
        kwargs (dict): Keyword arguments passed to the function.

    Returns:
        dict: A dictionary mapping parameter names to their values.
    """
        
    params = inspect.signature(function).parameters.keys()

    paramsDict = {}
    for i, name in enumerate(params):
        if i < len(args): paramsDict[name] = args[i]
        elif name in kwargs: paramsDict[name] = kwargs[name]

    return paramsDict

def formatMessage(message, paramsDict):
    """
    Format the error message using the provided parameters dictionary.

    Args:
        message (str): The base error message to format.
        paramsDict (dict): Dictionary containing parameter names and values for formatting.

    Returns:
        str: The formatted error message.
    """
        
    try: formattedMessage = message.format(**paramsDict)
    except KeyError: formattedMessage = f"{message} || (Error formatting message)"

    return formattedMessage

def getErrorDetails(customTraceback):
    """
    Extract error details from the traceback.

    Args:
        tb (traceback): The traceback object from the caught exception.

    Returns:
        tuple: A tuple containing the source code line, line number, and file name where the error occurred.
    """

    tb = traceback.extract_tb(customTraceback)
    lineNumber = tb[-1].lineno if tb else "unknown"
    fileName   = tb[-1].filename if tb else "unknown"
    sourceCode = linecache.getline(fileName, lineNumber).strip() if fileName != "unknown" else "unknown"

    return sourceCode, lineNumber, fileName

def displayErrorMessage(
    message: str,
    exception: str,
    functionName: str,
    sourceCode: str,
    lineNumber: str,
    fileName: str,
    displayType: Literal["print", "tkinter"],
):
    """
    Display the error message using the specified method.

    Args:
        message (str): The base error message.
        exception (str): The exception message.
        functionName (str): The name of the function where the error occurred.
        sourceCode (str): The source code line that caused the error.
        lineNumber (str): The line number of the error.
        fileName (str): The file name where the error occurred.
        displayType (Literal["print", "tkinter"], optional):
            The method to display the error details.
            - "print": Prints the detailed error report to the console (default).
            - "tkinter": Displays the error details in a Tkinter messagebox.showerror().
            Defaults to "print".
    """

    error = f"""
        ERROR: {message}
        EXCEPTION: {exception}
        FUNCTION: {functionName}
        CODE: {sourceCode}
        LINE: {lineNumber}
        FILE: {fileName}
    """
    
    if displayType == "print": 
        print(f"""
            \n
            \\------------------------------------------------------//
            {error}
            //------------------------------------------------------\\
            \n
        """)

    elif displayType == "tkinter":
        messagebox.showerror(
            message,
            error
        )
        
    else:
        print(f"""
            \n
            \\!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!//
                ERROR: Invalid error handling method specified. Defaulting to print.
                FUNCTION: exceptionHandler.
                SOLUTION: Specify the correct method to the handler function.
            //!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\\
            \n
        """)
