from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Модуль конфигурации API сервиса """
    
    # Подключение к БД (PostgreSQL) 
    DATABASE_URL: str = "postgresql://postgres:changeme@localhost:5432/url_shortener"
    
    # Подключение к Redis для кэширования
    REDIS_URL: str = "redis://localhost:6379/0"
    """Формат: redis://<host>:<port>/<db_number>
    
    Параметры:
    - host: адрес сервера Redis (localhost или IP)
    - port: порт (по умолчанию 6379)
    - db_number: номер базы данных
    """ 
    
    # Ключ для JWT токенов
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Алгоритм шифрования 
    ALGORITHM: str = "HS256"
    
    # Время жизни токена
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Адрес сервиса 
    BASE_URL: str = "http://localhost:8000"

    
    class Config:
        env_file = ".env"
    """
    Внутренняя конфигурация Pydantic Settings
        
    Параметры:
    - env_file: имя файла с переменными окружения (.env)
    """


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()