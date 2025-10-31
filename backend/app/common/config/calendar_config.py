# common/config/calendar_config.py
# Конфигурация календаря для работы с российскими рабочими днями и праздниками
from datetime import date, timedelta
from workalendar.europe import Russia
from typing import List


class RussianCalendar:
    """
    Класс для работы с российским производственным календарем.

    Обеспечивает функциональность для определения рабочих дней, 
    расчета рабочих периодов и учета праздников.
    """

    def __init__(self):
        """Инициализация календаря России из библиотеки workalendar."""
        self.calendar = Russia()

    def is_working_day(self, date_obj: date) -> bool:
        """
        Проверка, является ли день рабочим с учетом праздников и выходных.

        Args:
            date_obj (date): Дата для проверки

        Returns:
            bool: True если день рабочий, False если выходной или праздничный
        """
        return self.calendar.is_working_day(date_obj)

    def add_working_days(self, start_date: date, days_to_add: int) -> date:
        """
        Добавление указанного количества рабочих дней к начальной дате.

        Args:
            start_date (date): Начальная дата
            days_to_add (int): Количество рабочих дней для добавления

        Returns:
            date: Результирующая дата после добавления рабочих дней
        """
        return self.calendar.add_working_days(start_date, days_to_add)

    def get_working_days_between(self, start_date: date, end_date: date) -> int:
        """
        Расчет количества рабочих дней между двумя датами.

        Args:
            start_date (date): Начальная дата периода
            end_date (date): Конечная дата периода

        Returns:
            int: Количество рабочих дней в периоде
        """
        return self.calendar.get_working_days_delta(start_date, end_date)


# Создание глобального экземпляра календаря для использования во всем приложении
russian_calendar = RussianCalendar()