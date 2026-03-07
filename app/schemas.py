from pydantic import BaseModel, HttpUrl, EmailStr
from datetime import datetime
from typing import Optional

"""
Модуль Pydantic схем для валидации данных.

Содержит:
- Схемы для пользователей (регистрация, вход, ответ)
- Схемы для токенов (JWT)
- Схемы для ссылок (CRUD операции, статистика)
- Схемы для поиска

""" 

# USER SCHEMAS

class UserBase(BaseModel):
    """Базовая схема пользователя"""
    email: EmailStr


class UserCreate(UserBase):
    """Данные для регистрации пользователя"""
    password: str


class UserLogin(BaseModel):
    """Данные для входа"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Данные пользователя в ответе"""
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# TOKEN SCHEMAS

class Token(BaseModel):
    """Ответ при успешном входе"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Данные из токена"""
    email: Optional[str] = None


# LINK SCHEMAS

class LinkBase(BaseModel):
    """Базовая схема ссылки"""
    original_url: HttpUrl


class LinkCreate(LinkBase):
    """Данные для создания ссылки"""
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None
    project_name: Optional[str] = None


class LinkUpdate(BaseModel):
    """Данные для обновления ссылки"""
    original_url: Optional[HttpUrl] = None
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None
    project_name: Optional[str] = None


class LinkResponse(LinkBase):
    """Ответ с информацией о ссылке"""
    short_code: str
    custom_alias: Optional[str] = None
    click_count: int = 0
    created_at: datetime
    last_accessed_at: Optional[datetime] = None
    short_url: str
    project_name: Optional[str] = None

    class Config:
        from_attributes = True


class LinkStats(BaseModel):
    """Статистика по ссылке"""
    original_url: str
    short_code: str
    click_count: int
    created_at: datetime
    last_accessed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# SEARCH SCHEMAS

class LinkSearch(BaseModel):
    """Результат поиска"""
    short_code: str
    original_url: str
    click_count: int
    created_at: datetime
    short_url: str

    class Config:
        from_attributes = True