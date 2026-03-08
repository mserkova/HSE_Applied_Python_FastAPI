import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.config import get_settings


# Создаем тестовую базу данных 
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


def override_get_settings():
    class TestSettings:
        DATABASE_URL = SQLALCHEMY_DATABASE_URL
        REDIS_URL = "redis://localhost:6379/0"
        SECRET_KEY = "test-secret-key-for-testing-only"
        ALGORITHM = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES = 30
        BASE_URL = "http://test"
    
    return TestSettings()


# Применяем зависимости
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_settings] = override_get_settings

# БД будет создаваться перед каждым тестом
@pytest.fixture(scope="function")
def db_session(): 
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)

# TestClient для тестирования АPI
@pytest.fixture(scope="function")
def client(db_session):
    with TestClient(app) as test_client:
        yield test_client