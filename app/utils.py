import string
import random
import bcrypt 
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from app.config import settings

"""
Модуль вспомогательных утилит для сервиса

Содержит функции для:
- генерации уникальных коротких кодов ссылок
- хэширования и проверки паролей
- создания и декодирования токенов (аутентификация)


"""


def generate_short_code(length: int = 6) -> str:
    """
    Генерирует случайный короткий код из 6 символов для длинной ссылки из букв (a-z, A-Z) и чисел (0-9).
    Пример: 'abc123', 'xY7kL9'
    """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие пароля его хэшу
    
    """
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def get_password_hash(password: str) -> str:
    """
    Создает криптографический пароль хэш для регистрации пользователя и безопасного хранения пароля в БД
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Создает токен для аутентификации пользователя 
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Расшифровывает JWT токен и возвращает данные.
    Если токен невалидный — возвращает None
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None



