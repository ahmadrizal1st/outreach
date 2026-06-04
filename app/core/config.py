import os
from dotenv import load_dotenv, set_key
from cryptography.fernet import Fernet

load_dotenv()

class Settings:
    
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/client_finder.db")

    FOLLOWUP_INTERVAL_DAYS: int = int(os.getenv("FOLLOWUP_INTERVAL_DAYS", 3))
    MAX_FOLLOWUP: int = int(os.getenv("MAX_FOLLOWUP", 2))

    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

settings = Settings()

if not settings.ENCRYPTION_KEY:
    new_key = Fernet.generate_key().decode('utf-8')
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    
    if not os.path.exists(env_path):
        with open(env_path, "w") as f:
            f.write(f"ENCRYPTION_KEY={new_key}\n")
    else:
        set_key(env_path, "ENCRYPTION_KEY", new_key)
    
    settings.ENCRYPTION_KEY = new_key
