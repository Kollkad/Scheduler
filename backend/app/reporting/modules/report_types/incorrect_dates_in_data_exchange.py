# backend/app/reporting/modules/report_types/incorrect_dates_in_data_exchange.py
"""
Репорт о некорректных датах, обнаруженных при экспорте данных.

Определяет, для каких ролей следует сохранять репорт при обнаружении
проблемных дат в процессе сохранения Parquet-файлов.
"""
from typing import Optional

from backend.app.administration_settings.modules.user_models import UserRole


def should_save_date_problems(user_role: Optional[UserRole]) -> bool:
    """
    Проверяет, нужно ли сохранять репорт о проблемных датах.

    Репорт сохраняется только для руководителей и администраторов.
    Рядовые сотрудники не должны получать репорты о проблемах в данных.

    Args:
        user_role: Роль пользователя (строка из UserRole)

    Returns:
        bool: True если нужно сохранять репорт
    """
    if not user_role:
        return False
    allowed_roles = [UserRole.ADMIN, UserRole.MANAGER]
    return user_role in allowed_roles


