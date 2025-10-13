from databases import Database
from sqlalchemy import create_engine, MetaData
from backend.config import DATABASE_URL

# Асинхронное соединение для запросов
database = Database(DATABASE_URL)

# Синхронный engine для инициализации таблиц
engine = create_engine(DATABASE_URL)

metadata = MetaData()  # если нужно, можно импортировать сюда metadata из models

async def connect():
    await database.connect()

async def disconnect():
    await database.disconnect()
