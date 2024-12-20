# Используем официальный Python-образ
FROM python:3.12-slim

# Устанавливаем необходимые системные зависимости
RUN apt-get update && apt-get install -y libpq-dev gcc curl && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Устанавливаем рабочую директорию
WORKDIR /app

# Оптимизация: устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Копируем только файлы Poetry для установки зависимостей
COPY pyproject.toml poetry.lock ./

# Устанавливаем зависимости без запуска виртуального окружения
RUN poetry config virtualenvs.create false && poetry install --no-root --no-interaction --no-ansi

# Копируем остальные файлы проекта
COPY . .
