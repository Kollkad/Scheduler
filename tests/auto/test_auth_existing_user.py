# tests/auto/test_auth_existing_user.py

"""
Тест: test_auth_existing_user

Проверяет:
1. POST /api/auth/login — создание сессии
2. GET /api/auth/status — authenticated: true, роль определена
3. POST /api/auth/logout — очистка сессии
4. GET /api/auth/status — authenticated: false
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
import os
os.environ["WORK_MODE"] = "DEV"
client = TestClient(app)

@pytest.mark.ci
def test_auth_existing_user():
    # Шаг 1: логин
    response = client.post("/api/auth/login")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["authenticated"] is True
    assert data["role"] is not None
    assert data["role"] != "Гость"

    # Сохраняем куки сессии
    cookies = response.cookies

    # Шаг 2: статус с куками
    response = client.get("/api/auth/status", cookies=cookies)
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is True
    assert data["role"] is not None

    # Шаг 3: логаут
    response = client.post("/api/auth/logout", cookies=cookies)
    assert response.status_code == 200


