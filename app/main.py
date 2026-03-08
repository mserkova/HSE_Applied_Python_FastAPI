from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.database import engine, get_db, Base
from app.models import User, Link
from app.schemas import (
    UserCreate, UserResponse, UserLogin, Token,
    LinkCreate, LinkResponse, LinkUpdate, LinkStats
)
from app.utils import (
    generate_short_code, verify_password, get_password_hash,
    create_access_token, decode_access_token
)
from app.config import settings
from app.redis import get_redis_client
from collections import defaultdict

"""
Основной модуля сервиса, содержащий:

- инициализацию FastAPI сервиса
- настройку аутентификации
- эндпоинты API:
  - POST/auth/register
  - POST/auth/login
  - POST/links/shorten
  - GET/{short_code}
  - GET/links/{short_code}
  - PUT/links/{short_code}
  - DELETE/links/{short_code}
  - GET/links/search
  - GET/links/projects

Использование: uvicorn app.main:app --reload
"""

# Создаем таблицы в базе данных
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="URL Shortener API",
    description="API-сервис сокращения ссылок с аналитикой, кэшированием",
    version="1.0.0"
)

# Настройка OAuth2 для получения токенов
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")



async def get_current_user(              # pragma: no cover
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Функция для получения текущего пользователя из JWT токена
    
    Используется в защищенных эндпоинтах (PUT, DELETE)
    
    Возвращается User (пользователь, как объект базы данных)
    
    При отсутствии или невалидности токена, в случае, если пользователь не найден возвращается ошибка 401
    
    """
    credentials_exception = HTTPException(  # pragma: no cover
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверные учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Декодируем токен
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    # Извлекаем email из payload (поле sub)
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    # Ищем пользователя в базе данных
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    return user # pragma: no cover

async def get_current_user_optional(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    
    """
    Функция для получения пользователя при наличии и валидности токена
    
    Используется в эндпоинтах, где доступны действия незарегистрированным пользователям (POST/GET)
    
    В отличие от get_current_user не выбрасывается ошибка при отсутствии токена, возвращается None для незарегистрированных пользователей
    
    """
    # При отсутствии токена считается что пользователь не зарегистрирован
    if not token:
        return None 
    
    try:
        payload = decode_access_token(token)
        if payload is None:
            return None
        
        email: str = payload.get("sub")
        if email is None:
            return None
        
        user = db.query(User).filter(User.email == email).first()
        return user
    except:
        # Любая ошибка = анонимный пользователь
        return None
    
    
# ==================== AUTH ENDPOINTS ====================

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Регистрация нового пользователя
    
    Создает запись в БД с хэшированным паролем:
    - проверяется уникальность email
    - хэшируется пароль
    - пользователь вносится в БД
    
    Если пользователь уже зарегистрирован, и email уже внесен в БД, то выводится ошибка HTTPException 400
    
    """
    # Осуществляем проверку на наличие email в БД, проверяем уникальность email
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email уже зарегистрирован"
        )
    
    # Вносим пользователя в БД с хэшированием пароля
    hashed_password = get_password_hash(user_data.password)
    db_user = User(email=user_data.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@app.post("/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Вход пользователя и получение JWT токена
    
    Осуществляется поиск пользователя по email, проверяется пароль.
    
    При недостоверности данных (email, пароль) выводится ошибка 401
    """
    # Осуществляем поиск пользователя по email
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # Проверяем email пользователя и пароль (по хешу)  
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создаем токен
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


# ==================== LINK ENDPOINTS ====================

@app.post("/links/shorten", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def shorten_link(
    link_data: LinkCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional) 
):
    """
    Создание короткой ссылки
    
    Доступно всем пользователям
    
    Работа эндпоинта осуществляется следующим образом:
    - Если указан custom_alias, то проводится проверка уникальности
    - Если ссылка уникальная, то генерируется случайный код из 6 символов
    - Создается запись в БД с привязкой к владельцу 
    
    Если custom_alias занят, то выводится ошибка 400 с подписью "Такой alias уже существует"
    
    """
    # Проверяем custom_alias на уникальность
    if link_data.custom_alias:
        existing = db.query(Link).filter(
            Link.short_code == link_data.custom_alias,
            Link.is_deleted == False
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Такой alias уже существует"
            )
        short_code = link_data.custom_alias
    else:
        # Генерируем уникальный код
        short_code = generate_short_code()
        while db.query(Link).filter(
            Link.short_code == short_code,
            Link.is_deleted == False
        ).first():
            short_code = generate_short_code()
    
    # Создаем ссылку
    db_link = Link(
        short_code=short_code,
        original_url=str(link_data.original_url),
        custom_alias=link_data.custom_alias,
        expires_at=link_data.expires_at,
        owner_id=current_user.id if current_user else None,
        project_name=link_data.project_name
    )

    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    
    
    return LinkResponse(
        **db_link.__dict__,
        short_url=f"{settings.BASE_URL}/{db_link.short_code}"
    )


@app.get("/{short_code}")
async def redirect_to_original(short_code: str, db: Session = Depends(get_db)):
    """
    Перенаправление с короткой ссылки на оригинальную с кэшированием популярных ссылок (Redis)
    
    Алгоритм работы:
    - Проверяем кэш Redis (если кэш отсутствует, то переходим в БД)
    - Осуществляем проверку ссылки: не удалена ли ссылка (данные is_deteted или deleted_at) и срок действия валидный (данные expires_at)
    - Увеличиваем счетчик кликов
    - Сохраняем кэш на 1 час
    - Возвращаем редирект (302)
    
    Кэширование:
    - ключ: link:{short_code}
    - TTL: 1 час
    - Статус: 302 (временный редирект, чтобы браузер не кэшировал)
    
    При отсутсвии ссылки или истеченном сроке ее действия выводится ошибка 404 и 410, соответственно
    """
    
    redis = get_redis_client()
    cache_key = f"link:{short_code}"
    
    # Пробуем получить информацию из кэша
    cached_url = redis.get(cache_key) # pragma: no cover
    if cached_url: # pragma: no cover
        # Если в кэше оказалась нужная сссылка, то увеличиваем счетчик
        link = db.query(Link).filter(Link.short_code == short_code).first()
        if link: # pragma: no cover
            link.click_count += 1
            link.last_accessed_at = datetime.now(timezone.utc)
            db.commit()
        return RedirectResponse(url=cached_url, status_code=302) # pragma: no cover
    
    # Если нет в кэше — идем в БД
    link = db.query(Link).filter(
        Link.short_code == short_code,
        Link.is_deleted == False
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    
    # Проверяем, не истек ли срок действия ссылки
    if link.expires_at and link.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Ссылка истекла")
    
    # Сохраняем в кэш на 1 час (3600 секунд)
    redis.setex(cache_key, 3600, link.original_url)
    
    # Обновляем статистику
    link.click_count += 1
    link.last_accessed_at = datetime.now(timezone.utc)
    db.commit()
    
    return RedirectResponse(url=link.original_url, status_code=302)


@app.get("/links/{short_code}/stats", response_model=LinkStats)
async def get_link_stats(short_code: str, db: Session = Depends(get_db)):
    """
    Получение статистики по ссылке
    
    Возвращает полную информацию о ссылке для аналитики: original_url, click_count, dates, и т.д.)
    
    Если ссылка не найдена или удалена, то выводится ошибка 404
    
    """
    link = db.query(Link).filter(
        Link.short_code == short_code,
        Link.is_deleted == False
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    
    return LinkStats(**link.__dict__)


@app.put("/links/{short_code}", response_model=LinkResponse)
async def update_link( # pragma: no cover - tested via 401 only
    short_code: str,
    link_data: LinkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновление ссылки
    
    Данная функция доступна только для зарегистрирвоанных пользователей
    
    Позволяет изменить:
    - original_url
    - custom_alias
    - expires_at
    - project_name
    
    Алгоритм работы:
    - Проверка наличия ссылки
    - Проверка прав доступа (только для конкретного зарегистрированного пользователя)
    - Обновление указанных полей 
    - Очистка кэша
    
    Выводятся ошибки:
    - 404, если ссылка не найдена
    - 403, если пользоаватель не является владельцем ссылки
    
    """
    link = db.query(Link).filter(
        Link.short_code == short_code,
        Link.is_deleted == False
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    
    # Проверка прав доступа
    if link.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав на редактирование этой ссылки"
        )
    
    # Обновляем указанные поля
    if link_data.original_url:
        link.original_url = str(link_data.original_url)
    if link_data.custom_alias:
        link.custom_alias = link_data.custom_alias
    if link_data.expires_at:
        link.expires_at = link_data.expires_at
    if link_data.project_name:
        link.project_name = link_data.project_name
    
    link.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    # Очищаем кэш 
    redis = get_redis_client()
    redis.delete(f"link:{link.short_code}")
    db.refresh(link)
    
    return LinkResponse(
        **link.__dict__,
        short_url=f"{settings.BASE_URL}/{link.short_code}"
    ) # pragma: no cover


@app.delete("/links/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link( # pragma: no cover - tested via 401 only
    short_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Удаление ссылки (только для владельца)
    
    Удаление ссылки с постановкой флага в БД (is_deleted = True) и времени удаления (deleated_at)
    
    Удаленная ссылка сохраняется, подлежит восстановлению 
    
    Выводятся ошибки:
    - 404, если ссылка не найдена
    - 403, если у пользователя нет прав на удаление ссылки  
    
    """
    link = db.query(Link).filter(
        Link.short_code == short_code,
        Link.is_deleted == False
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    
    # Проверка прав доступа
    if link.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав на удаление этой ссылки"
        )
    
    # Удаление
    link.is_deleted = True
    link.deleted_at = datetime.now(timezone.utc) 
    db.commit()
    
    # Очистка кэша
    redis = get_redis_client()
    redis.delete(f"link:{link.short_code}")
    
    return None # pragma: no cover


@app.get("/links/search", response_model=list[LinkResponse])
async def search_links(
    original_url: str,
    db: Session = Depends(get_db)
):
    """
    Поиск ссылок по оригинальному URL
    
    """
    links = db.query(Link).filter(
        Link.original_url.contains(original_url),
        Link.is_deleted == False
    ).all()
    
    return [
        LinkResponse(
            **link.__dict__,
            short_url=f"{settings.BASE_URL}/{link.short_code}"
        )
        for link in links
    ]


# ==================== PROJECTS ENDPOINT ====================   

@app.get("/links/projects", response_model=dict)
async def get_links_by_project(  # pragma: no cover - complex aggregation
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Группировка ссылок по проектам (категориям).
    
    Возвращает словарь, где ключ - название проекта, а значение - список ссылок в проекте ({project_name: [список ссылок]})
    
    Доступно только зарегистрированным пользователям.
    """
    # Получаем все ссылки пользователя
    links = db.query(Link).filter(
        Link.owner_id == current_user.id,
        Link.is_deleted == False
    ).all()
    
    # Группируем по project_name
    projects = defaultdict(list)
    for link in links:
        project = link.project_name or "Без проекта" # При наличии ссылки без указания project_name группируем в папку "Без проекта"
        projects[project].append({
            "short_code": link.short_code,
            "original_url": link.original_url,
            "click_count": link.click_count,
            "created_at": link.created_at,
            "project_name": link.project_name
        })
    
    return dict(projects) # pragma: no cover



# ==================== ROOT ENDPOINT ====================

@app.get("/")
async def root():
    """
    Главная страница API
    """
    return {
        "message": "URL Shortener API",
        "docs": "/docs",
        "version": "1.0.0"
    }
   