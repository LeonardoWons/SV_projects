import time
import functools

import asyncio
from typing import Literal, Callable, Optional, Any

from handler.util\
    import getParamsDict, formatMessage, getErrorDetails, displayErrorMessage

#? ---------- Wrapper factory functions ---------- #?
def createAsyncWrapper(
    function: Callable,
    message: str,
    type: Literal["print", "tkinter"] = "print",
    errorReturn: Optional[Any] = None,
    finallyFunction: Optional[Callable] = None,
    retry: bool = False,
    retryDelay: int = 1,
    retryAttempts: int | Literal["infinite"] = 1,
):
    """
    Create a wrapper for asynchronous functions with retry logic.

    Args:
        function (Callable): The function to be wrapped.
        message (str): The base error message to display.
        type (Literal["print", "tkinter"]): The method to display the error details.
        errorReturn (Optional[Any]): The value to return from the decorated function if an exception is caught.
        finallyFunction (Optional[Callable]): A callable to be executed in the `finally` block.
        retry (bool): Whether to retry the function when an exception occurs.
        retryDelay (int): Time in seconds to wait between retry attempts.
        retryAttempts (int | Literal["infinite"]): Maximum number of retry attempts.

    Returns:
        Callable: The wrapped asynchronous function.
    """

    @functools.wraps(function)
    async def asyncWrapper(*args, **kwargs):
        maxAttempts = 0
        currentAttempt = 0

        if retry:
            if retryAttempts == "infinite": maxAttempts = float('inf')
            else: maxAttempts = 1 + retryAttempts

        else:
            maxAttempts = 1

        paramsDict = getParamsDict(function, args, kwargs)

        try:
            while True:
                currentAttempt += 1

                try:
                    return await function(*args, **kwargs)
                
                except Exception as e:
                    formattedMessage = formatMessage(message, paramsDict)
                    sourceCode, lineNumber, fileName = getErrorDetails(e.__traceback__)
                    displayErrorMessage(formattedMessage, e, function.__name__, sourceCode, lineNumber, fileName, type)

                    if currentAttempt < maxAttempts:
                        if retryDelay > 0: await asyncio.sleep(retryDelay)
                        continue

                    if callable(errorReturn): return errorReturn()
                    return errorReturn
                        
        finally:
            if finallyFunction: finallyFunction()

    return asyncWrapper

def createSyncWrapper(
    function: Callable,
    message: str,
    type: Literal["print", "tkinter"] = "print",
    errorReturn: Optional[Any] = None,
    finallyFunction: Optional[Callable] = None,
    retry: bool = False,
    retryDelay: int = 1,
    retryAttempts: int | Literal["infinite"] = 1,
):
    """
    Create a wrapper for synchronous functions with retry logic.

    Args:
        function (Callable): The function to be wrapped.
        message (str): The base error message to display.
        type (Literal["print", "tkinter"]): The method to display the error details.
        errorReturn (Optional[Any]): The value to return from the decorated function if an exception is caught.
        finallyFunction (Optional[Callable]): A callable to be executed in the `finally` block.
        retry (bool): Whether to retry the function when an exception occurs.
        retryDelay (int): Time in seconds to wait between retry attempts.
        retryAttempts (int | Literal["infinite"]): Maximum number of retry attempts.

    Returns:
        Callable: The wrapped synchronous function.
    """
        
    @functools.wraps(function)
    def syncWrapper(*args, **kwargs):
        maxAttempts = 0
        currentAttempt = 0

        if retry:
            if retryAttempts == "infinite": maxAttempts = float('inf')
            else: maxAttempts = 1 + retryAttempts

        else:
            maxAttempts = 1

        paramsDict = getParamsDict(function, args, kwargs)

        try:
            while True:
                currentAttempt += 1

                try:
                    return function(*args, **kwargs)
                
                except Exception as e:
                    formattedMessage = formatMessage(message, paramsDict)
                    sourceCode, lineNumber, fileName = getErrorDetails(e.__traceback__)
                    displayErrorMessage(formattedMessage, e, function.__name__, sourceCode, lineNumber, fileName, type)

                    if currentAttempt < maxAttempts:
                        if retryDelay > 0: time.sleep(retryDelay)
                        continue

                    if callable(errorReturn): return errorReturn()
                    return errorReturn
                        
        finally:
            if finallyFunction: finallyFunction()

    return syncWrapper