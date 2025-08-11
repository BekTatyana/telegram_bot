from dotenv import load_dotenv
import os


load_dotenv()


class Config:
    """Класса для хранения настроек"""

    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    DATABASE_URL = os.getenv("DATABASE_URL", "")


config = Config()
