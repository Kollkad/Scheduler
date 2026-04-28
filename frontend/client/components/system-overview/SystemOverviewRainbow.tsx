// frontend/client/components/system-overview/SystemOverviewRainbow.tsx

export function SystemOverviewRainbow() {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-text-primary">Цветовая система оценки (Rainbow)</h2>
      <p className="text-text-primary">
        Rainbow - это визуальная система оценки сроков сопровождения дел, где каждый цвет соответствует 
        определенному состоянию дела. Система позволяет быстро оценить общую ситуацию 
        и выявить проблемные зоны.
      </p>

      <div className="bg-bg-light-green p-4 rounded-lg border border-green-dark">
        <h3 className="font-semibold text-green-dark mb-3">Возможности раздела Rainbow:</h3>
        <ul className="list-disc list-inside text-green-dark text-sm space-y-2">
          <li>Нажмите на любой цветной столбец диаграммы для просмотра дел соответствующего статуса</li>
          <li>Используйте форму фильтров для детальной настройки отчета</li>
          <li>Анализируйте распределение дел по цветам для выявления проблемных зон</li>
          <li>Нажмите на строку в таблице для перехода к детальной информации о деле</li>
        </ul>
      </div>

      <div className="bg-white p-4 rounded-lg border border-border-default">
        <h3 className="font-semibold text-text-primary mb-3">Условия определения цветов:</h3>
        
        <div className="text-sm text-text-secondary mb-4">
          <p className="font-medium mb-2">Общие условия:</p>
          <ul className="list-disc list-inside ml-4">
            <li>Только дела с категорией "Иск от Банка"</li>
            <li>Нет дел со статусом "Закрыто"</li>
            <li>Нет дел со статусом "Ошибка-Дубликат"</li>
            <li>Нет дел со статусом "Отозвано инициатором"</li>
          </ul>
        </div>

        <div className="space-y-4">
          <ColorItem color="bg-black" label="ИК" description='Вид запроса содержит "залог"' />
          <ColorItem color="bg-gray-400" label="Серый" description='Статус дела = "Переоткрыто"' />
          <ColorItem color="bg-green-500" label="Зеленый" description='Статус дела = "Суд. акт вступил в законную силу" и заполнена "Фактическая дата передачи ИД"' />
          <ColorItem color="bg-yellow-400" label="Желтый" description='Статус дела = "Условно закрыто" и заполнена "Фактическая дата передачи ИД"' />
          <ColorItem color="bg-orange-500" label="Оранжевый" description='Статус дела = "Суд. акт вступил в законную силу" И НЕ заполнена "Фактическая дата передачи ИД"' />
          <ColorItem color="bg-blue-600" label="Синий" description='Способ судебной защиты = "Приказное производство" и прошло более 90 дней от "Дата последнего поступления запроса в ЮП"' />
          <ColorItem color="bg-red-500" label="Красный" description='"Дата последнего поступления запроса в ЮП" до 01.01.2025 года' />
          <ColorItem color="bg-purple-500" label="Лиловый" description='Способ судебной защиты = "Исковое производство" и прошло более 120 дней от "Дата последнего поступления запроса в ЮП"' />
          <ColorItem color="bg-white border border-gray-300" label="Белый" description="Все остальные дела для мониторинга и отработки в рабочем порядке, не подходящие под вышеперечисленные условия" />
        </div>
      </div>
    </div>
  );
}

function ColorItem({ color, label, description }: { color: string; label: string; description: string }) {
  return (
    <div className="flex items-start">
      <div className={`w-4 h-4 ${color} rounded mr-3 mt-0.5 flex-shrink-0`}></div>
      <div>
        <p className="font-medium text-sm">{label}</p>
        <p className="text-xs text-text-secondary">{description}</p>
      </div>
    </div>
  );
}