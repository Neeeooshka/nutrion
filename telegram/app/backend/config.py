# backend/config.py
from dotenv import load_dotenv
from urllib.parse import quote_plus
import os

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = quote_plus(os.getenv("POSTGRES_PASSWORD"))
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")

# формируем DATABASE_URL динамически
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
