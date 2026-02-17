import threading

class DataStore:
    """
    Thread-safe singleton container for sharing global data between components.
    
    This class implements a centralized thread-safe storage mechanism for application-wide
    data that needs to be shared between multiple components, threads, and API endpoints.
    It uses a singleton pattern to ensure only one instance exists throughout the application
    lifecycle, and employs thread locks to prevent race conditions during concurrent access.
    
    Key features:
    - Thread-safe access to shared data using internal locks
    - Singleton pattern ensures consistent state across the application
    - Dictionary-based storage for flexible key-value pairs
    - Default value support for graceful handling of missing keys
    
    Usage:
        # Get the global instance (typically done in globals.py)
        store = DataStore.get_instance()
        
        # Store values
        store.set("client", modbus_client)
        store.set("tugger_id", "123456")
        
        # Retrieve values (with optional default)
        client = store.get("client")
        configuration = store.get("config", default={})
    
    Thread safety:
        All operations acquire the internal lock before accessing the underlying
        data dictionary, ensuring consistent reads and writes even during
        concurrent access from multiple threads.
    """

    _instance = None
    _lock = threading.Lock()
    _data = {}
    
    @classmethod
    def getInstance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def set(self, key, value):
        with self._lock:
            self._data[key] = value
    
    def get(self, key, default=None):
        with self._lock:
            return self._data.get(key, default)