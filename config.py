import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.absolute()
CHROMA_PERSIST_DIR = BASE_DIR / "chroma_data"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DATABASE"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}


def get_connection_string():
    cfg = POSTGRES_CONFIG
    return f"postgresql://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['database']}"


def validate_config():
    missing = []
    if not POSTGRES_CONFIG["database"]:
        missing.append("POSTGRES_DATABASE")
    if not POSTGRES_CONFIG["user"]:
        missing.append("POSTGRES_USER")
    if missing:
        raise ValueError(f"Missing required configuration: {', '.join(missing)}")

