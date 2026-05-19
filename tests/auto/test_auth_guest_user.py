# tests/auto/test_auth_guest_user.py

"""
Тест: test_auth_guest_user

Проверяет GET /api/auth/status для гостя.
Через dependency_overrides подменяет get_current_user на гостевую сессию.
"""

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.administration_settings.modules.user_models import UserSession
from backend.app.administration_settings.modules import authorization_logic
import pytest

client = TestClient(app)

@pytest.mark.ci
def test_auth_guest_user():
    # все роуты видят гостя
    async def mock_get_current_user(request=None):
        user = UserSession()
        user.set_guest()
        return user

    app.dependency_overrides[authorization_logic.get_current_user] = mock_get_current_user

    response = client.get("/api/auth/status")
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is False
    assert data["role"] == "Гость"

    app.dependency_overrides.clear()


