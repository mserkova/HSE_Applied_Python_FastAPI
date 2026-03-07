import redis
from functools import lru_cache
from app.config import settings


@lru_cache()
def get_redis_client() -> redis.Redis:
    """
    Модуль создания и кэширования подключения к Redis
    """
    client = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True, 
        socket_connect_timeout=5
    )
    return client