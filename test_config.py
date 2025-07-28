from config import BaseConfig

class TestConfig(BaseConfig):
    # Override with empty model paths for testing basic startup
    MODEL_PATHS = []