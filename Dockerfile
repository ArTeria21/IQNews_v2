# Используем официальный Python-образ
FROM python:3.12-slim

# Устанавливаем необходимые системные зависимости
RUN apt-get update && apt-get install -y libpq-dev gcc curl && rm -rf /var/lib/apt/lists/*

# Устанавливаем UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Устанавливаем рабочую директорию
WORKDIR /app

# Оптимизация: устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Копируем только файлы UV для установки зависимостей
COPY .python-version pyproject.toml uv.lock ./

# Устанавливаем зависимости без запуска виртуального окружения
RUN uv sync

# Копируем остальные файлы проекта
COPY . .
