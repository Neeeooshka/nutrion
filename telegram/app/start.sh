#!/bin/sh
set -e  # остановить выполнение при любой ошибке

echo "=== Инициализация базы данных ==="
python backend/init_db.py

echo "=== Запуск FastAPI ==="
uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info