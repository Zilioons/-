import time
import random
import hashlib
from threading import Lock

class UIDGenerator:
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.counter = 0
            return cls._instance
    
    def generate(self, prefix="UID"):
        with self._lock:
            self.counter += 1
            timestamp = int(time.time() * 1000)
            random_part = random.randint(1000, 9999)
            return f"{prefix}_{timestamp}_{self.counter}_{random_part}"
    
    def generate_task_id(self):
        return self.generate("TASK")
    
    def generate_cursor_id(self):
        return self.generate("CURSOR")
    
    def generate_result_id(self):
        return self.generate("RESULT")

uid_generator = UIDGenerator()