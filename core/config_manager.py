import configparser
import os

class ConfigManager:
    @staticmethod
    def load_config():
        config = configparser.ConfigParser()
        if not os.path.exists('config/config.ini'):
            raise FileNotFoundError("config.ini not found. Create from template.")
        config.read('config/config.ini')
        return config
