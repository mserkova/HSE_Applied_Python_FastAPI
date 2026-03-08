"""Нагрузочные тесты с Locust"""
from locust import HttpUser, task, between
import random
import string


class SimpleLinkTest(HttpUser):
    """Простой сценарий нагрузочного тестирования"""
    
    wait_time = between(1, 2)
    
    @task
    def redirect_random(self):
        """Переход по случайным коротким ссылкам"""
        # Генерируем случайный код
        code = ''.join(random.choices(string.ascii_lowercase, k=6))
        self.client.get(f"/{code}", name="/[short_code]")
    
    @task(2)
    def root_endpoint(self):
        """Запрос к главной странице"""
        self.client.get("/")