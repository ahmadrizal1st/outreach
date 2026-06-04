import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/client_finder.db")

    # Follow-up Settings
    FOLLOWUP_INTERVAL_DAYS: int = int(os.getenv("FOLLOWUP_INTERVAL_DAYS", 3))
    MAX_FOLLOWUP: int = int(os.getenv("MAX_FOLLOWUP", 2))

settings = Settings()
