from backend.models import metadata
from backend.db import engine

# создаем все таблицы
metadata.create_all(bind=engine)

print("Таблицы созданы!")
