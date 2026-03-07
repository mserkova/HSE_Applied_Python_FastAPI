from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

"""
Описание таблиц базы данных
"""

# Таблица с информацией о пользователях
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True) # уникальный номер пользователя 
    email = Column(String, unique=True, index=True, nullable=False) # почта пользователя
    hashed_password = Column(String, nullable=False) # зашифрованный пароль
    is_active = Column(Boolean, default=True) # активность пользователя 
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # дата регистрации

    # Связь с ссылками (один пользователь → много ссылок)
    links = relationship("Link", back_populates="owner")

# Между таблицей с пользовтаелем и таблицей с информацией о ссылках связь один ко многим, т.е. один пользователь - несколько ссылок

#  Таблица с информацией по ссылкам 
class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True) # уникальный номер ссылки
    short_code = Column(String, unique=True, index=True, nullable=False) # короткий код  
    original_url = Column(String, nullable=False) # длинная ссылка 
    custom_alias = Column(String, nullable=True) # уникальное название 
    expires_at = Column(DateTime(timezone=True), nullable=True) # дата истечения сслыки 
    click_count = Column(Integer, default=0) # количество кликов по ссылке
    last_accessed_at = Column(DateTime(timezone=True), nullable=True) # псоледний переход по ссылке
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # дата-время, когда создана ссылка
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) # дата-время обновления ссылки
    is_deleted = Column(Boolean, default=False) # флаг наличия/отстутствия факта удаления
    deleted_at = Column(DateTime(timezone=True), nullable=True) # дата-время удаления
    project_name = Column(String, nullable=True) # название проекта

    # Владелец ссылки (может быть NULL для незарегистрированных пользователей)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner = relationship("User", back_populates="links")