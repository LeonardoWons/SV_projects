import asyncio
from typing import Callable, Literal, Optional, Any

from handler.wrapper\
    import createAsyncWrapper, createSyncWrapper

def exceptionHandler(
    message: str,
    displayType: Literal["print", "tkinter"] = "print",
    errorReturn: Optional[Any] = None,
    finallyFunction: Optional[Callable] = None,
    retry: bool = False,
    retryDelay: int = 1,
    retryAttempts: int | Literal["infinite"] = 1,
):
    """
    A flexible decorator for comprehensive exception handling in synchronous and asynchronous functions.

    This decorator wraps a function to catch any exceptions that occur during its execution.
    It provides options for custom error messaging (including dynamic formatting with
    function arguments), different methods for displaying error details (console print,
    Tkinter pop-up), a specified return value in case of an error, and an optional
    function to execute in the `finally` block and retrying the function execution
    a specified number of times with a delay between attempts.

    The error report includes:
    - The custom formatted error message.
    - The exception type and message.
    - The name of the function where the error occurred.
    - The source code line that caused the error.
    - The line number and file name of the error.

    Args:
        message (str): The base error message to display. Can contain placeholders
                       (e.g., "{arg_name}") that will be formatted with the
                       decorated function's arguments if an exception occurs.
                       If formatting fails, a fallback message is used.
        displayType (Literal["print", "tkinter"], optional):
                       The method to display the error details.
                       - "print": Prints the detailed error report to the console (default).
                       - "tkinter": Displays the error details in a Tkinter messagebox.showerror().
                       Defaults to "print".
        errorReturn (Optional[Any], optional): The value to return from the decorated
                       function if an exception is caught. Defaults to None.
        finallyFunction (Optional[Callable], optional): A callable (function or method)
                       to be executed in the `finally` block, regardless of whether an
                       exception occurred or not. Defaults to None.
        retry (bool, optional): Whether to retry the function when an exception occurs.
                       Defaults to False.
        retryDelay (int, optional): Time in seconds to wait between retry attempts.
                       Defaults to 1.
        retryAttempts (int, optional): Maximum number of retry attempts.
                       Defaults to 1.

    Returns:
        Callable: The wrapped function with exception handling capabilities.

    Example:
        ```python
        @exceptionHandler("Failed to process data for item {item_id}", displayType="tkinter", errorReturn=False)
        def process_item(item_id: int, data: dict):
            # ... processing logic that might raise an exception ...
            if not data:
                raise ValueError("Data cannot be empty")
            return True

        process_item(123, {})  # If an error occurs, a Tkinter pop-up will show.
        ```
    """

    def decorator(function):
        """
        The actual decorator function that wraps the target function.

        Args:
            function (Callable): The function to be wrapped.

        Returns:
            Callable: The wrapped function.
        """

        isAsyncFunction = asyncio.iscoroutinefunction(function)

        if isAsyncFunction: 
            return createAsyncWrapper(
                function,
                message,
                displayType,
                errorReturn,
                finallyFunction,
                retry,
                retryDelay,
                retryAttempts
            )
        
        return createSyncWrapper(
            function,
            message,
            displayType,
            errorReturn,
            finallyFunction,
            retry,
            retryDelay,
            retryAttempts
        )

    return decorator