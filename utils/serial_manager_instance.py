# serial_manager_instance.py
from utils.serial_manager import SerialManager

class SingletonSerialManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SerialManager()
        return cls._instance

serial_manager = SingletonSerialManager.get_instance()