// frontend/client/components/system-overview/SystemOverviewComparison.tsx

export function SystemOverviewComparison() {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-text-primary">Сравнение периодов</h2>
      <p className="text-text-secondary">
        Данный раздел позволяет анализировать динамику показателей между текущим 
        и предыдущим отчетным периодом.
      </p>

      <div className="bg-bg-light-green p-4 rounded-lg border border-green-dark">
        <h3 className="font-semibold text-green-dark mb-2">Возможности раздела:</h3>
        <ul className="list-disc list-inside text-green-dark text-sm space-y-2">
          <li>Сравнение количества дел по цветам между периодами</li>
          <li>Анализ динамики сроков сопровождения</li>
          <li>Отслеживание изменений в эффективности работы</li>
          <li>Выявление тенденций и проблемных зон</li>
        </ul>
      </div>

      <h3 className="font-semibold text-text-primary">Как работает сравнение:</h3>
      <ol className="list-decimal list-inside text-text-secondary space-y-2">
        <li>Загрузите текущий отчетный период</li>
        <li>Загрузите отчет за предыдущий период (опционально)</li>
        <li>Система автоматически сопоставит данные по идентификаторам дел</li>
        <li>Получите наглядную визуализацию изменений</li>
      </ol>
    </div>
  );
}


