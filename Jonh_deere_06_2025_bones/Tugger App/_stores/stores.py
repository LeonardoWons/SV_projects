import threading

class DataStore:
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