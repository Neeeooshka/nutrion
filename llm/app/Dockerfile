FROM python:3.12-slim

# рабочая директория
WORKDIR /app

# скопировать зависимости
COPY requirements.txt .

# установить зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# скопировать весь код
COPY . .

# запуск
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8013"]
