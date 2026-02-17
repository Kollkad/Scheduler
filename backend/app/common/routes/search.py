# backend/app/common/routes/search.py
"""
Модуль поиска

Поиск кодов дел с частичным совпадением.
Источник данных:
- Детальный отчет
"""

from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/search", tags=["search"])

@router.get("/cases")
async def search_cases(
        q: str = Query(..., min_length=2, description="Поисковый запрос"),
        limit: int = Query(20, ge=1, le=100)
):
    """
    Поиск кодов дел в детальном отчете.

    Args:
        q: Минимум 2 символа
        limit: Максимум 100 результатов

    Returns:
        {
            "success": bool,
            "query": str,
            "results": List[{"caseCode": str, "source": str}],
            "total": int
        }
    """
    try:
        from backend.app.common.modules.data_manager import data_manager
        from backend.app.common.modules.utils import extract_unique_values

        results = []
        seen = set()

        # Поиск в детальном отчете
        df_detailed = data_manager.get_detailed_data()
        if df_detailed is not None and not df_detailed.empty:
            # Извлчечение уникальных значений из колонки CASE_CODE
            case_codes = extract_unique_values(df_detailed, 'CASE_CODE')
            for code in case_codes:
                if q.lower() in code.lower() and code not in seen:
                    results.append({"caseCode": code, "source": "detailed_report"})
                    seen.add(code)

        # Сортировка: сначала точные совпадения, потом по длине
        results.sort(key=lambda x: (
            -int(x["caseCode"].lower() == q.lower()),  # точное совпадение выше
            len(x["caseCode"]),  # короткие выше
            x["caseCode"]  # алфавитно
        ))

        return {
            "success": True,
            "query": q,
            "results": results[:limit],
            "total": len(results)
        }

    except Exception as e:
        print(f"Ошибка поиска: {e}")
        return {
            "success": False,
            "query": q,
            "results": [],
            "total": 0,
            "error": str(e)
        }