import pytest
from app.utils import generate_short_code


class TestGenerateShortCode:
    """Тесты для функции генерации короткого кода"""
    
    def test_generate_short_code_returns_string(self):
        """Тест: функция возвращает строку"""
        result = generate_short_code()
        assert isinstance(result, str)
    
    def test_generate_short_code_length(self):
        """Тест: длина кода равна 6 символам"""
        result = generate_short_code()
        assert len(result) == 6
    
    def test_generate_short_code_unique(self):
        """Тест: коды уникальны"""
        codes = [generate_short_code() for _ in range(100)]
        assert len(set(codes)) == 100
    
    def test_generate_short_code_alphanumeric(self):
        """Тест: код содержит только буквы и цифры"""
        result = generate_short_code()
        assert result.isalnum()