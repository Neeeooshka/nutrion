FROM python:3.11-slim

# рабочая директория
WORKDIR /app

# скопировать зависимости
COPY requirements.txt .

# установить зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# скопировать весь код
COPY . .

# скрипт запуска
COPY start.sh .
RUN chmod +x start.sh

# запуск
CMD ["./start.sh"]
