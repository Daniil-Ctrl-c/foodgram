# Foodgram

![Workflow Status](https://github.com/Daniil-Ctrl-c/foodgram/actions/workflows/main.yml/badge.svg)

## О проекте

Foodgram — платформа для публикации рецептов, добавления ингредиентов в корзину и скачивания списка покупок.

Функции:

* Регистрация и авторизация
* Публикация рецептов с изображениями
* Добавление рецептов в избранное
* Добавление ингредиентов в список покупок
* Скачивание списка покупок
* Поиск ингредиентов

## Стек технологий

* Python 3.9
* Django 3.2
* PostgreSQL
* React
* Docker, Docker Compose
* Nginx
* GitHub Actions (CI/CD)

## Как развернуть проект локально

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/Daniil-Ctrl-c/foodgram.git
   ```

2. Перейдите в папку проекта:
   ```bash
   cd foodgram
   ```

3. Создайте файл `.env` по примеру ниже.

4. Для локального запуска контейнеров:
   ```bash
   docker compose -f docker-compose.yml build && \
   docker compose -f docker-compose.yml up -d && \
   docker tag infra-backend daniilctrlc/foodgram_backend:latest && \
   docker tag infra-frontend daniilctrlc/foodgram_frontend:latest && \
   docker tag infra-gateway daniilctrlc/foodgram_gateway:latest && \
   docker push daniilctrlc/foodgram_backend:latest && \
   docker push daniilctrlc/foodgram_frontend:latest && \
   docker push daniilctrlc/foodgram_gateway:latest
   ```

5. Для запуска на сервере:
   ```bash
   docker-compose -f docker-compose.production.yml down && \
   docker-compose -f docker-compose.production.yml pull && \
   docker-compose -f docker-compose.production.yml up -d --force-recreate
   ```

## Переменные окружения

```env
DEBUG=False

DJANGO_SECRET_KEY=your_secret_key

DB_NAME=foodgram_db
DB_USER=foodgram_user
DB_PASSWORD=foodgram_password
DB_HOST=db
DB_PORT=5432

ALLOWED_HOSTS=localhost,127.0.0.1,backend,db,nginx,foodgram-daniil.duckdns.org

# Telegram
TELEGRAM_TOKEN=your_token
TELEGRAM_TO=your_chat_id
```

> **Важно:** в продакшене обязательно задайте `DJANGO_SECRET_KEY` вручную, чтобы не сбрасывались сессии и токены пользователей.

## CI/CD GitHub Actions

* Сборка Docker-образов backend/frontend/nginx
* Push в Docker Hub
* Копирование `docker-compose.production.yml` на сервер
* Перезапуск контейнеров и развёртывание обновлений
* Уведомление об успешном деплое в Telegram

## Админка

**ссылка:**
https://foodgram-daniil.duckdns.org/admin/

**почта:**
admin@gmail.com

**пароль:**
admin

## Автор

**Daniil-Ctrl-c**
