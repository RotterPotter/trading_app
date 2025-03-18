from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    # from .env vars
    POLYGON_API_KEY: str = os.getenv("POLYGON_API_KEY")

    EXECUTED_TRADES_FILE_PATH: str = "backtesting/output/executed_trades.json"
    LOGS_FILE_PATH: str = "backtesting/output/logs.csv"

settings = Settings()