from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Settings:
    POLYGON_API_KEY: str = os.getenv("POLYGON_API_KEY")
    EXECUTED_TRADES_FILE_PATH: str = os.getenv("EXECUTED_TRADES_FILE_PATH")
    LOGS_FILE_PATH: str = os.getenv("LOGS_FILE_PATH")

settings = Settings()