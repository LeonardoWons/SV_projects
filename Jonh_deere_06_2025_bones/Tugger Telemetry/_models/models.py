from pydantic import BaseModel

class LockRequestModel(BaseModel):
    """
    Request model for controlling the tugger's physical locking mechanism.
    
    This Pydantic model defines the structure of request bodies sent to the
    /api/lockRequest endpoint. It validates incoming JSON data and provides
    type checking for the lock control parameter.
    
    Attributes:
        unlock (bool): Control flag for the tugger's lock mechanism.
            - True: Request to unlock the tugger
            - False: Request to lock the tugger
    
    Example:
        ```json
        {
            "unlock": true
        }
        ```
    """

    unlock: bool  # True to unlock, False to lock