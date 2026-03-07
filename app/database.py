from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

"""
Модуль подключения и работы с базой данных

"""

# Создаем точку входа для подключения к базе данных PostgreSQL
engine = create_engine(settings.DATABASE_URL)

# Создаем функцию для создания сессий с базой данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создаём базовый класс для моделей
Base = declarative_base()


def get_db():
    """
    Функция для получения сессии БД
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()