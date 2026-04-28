// frontend/client/components/system-overview/SystemOverviewEmployeeTasks.tsx

export function SystemOverviewEmployeeTasks() {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-text-primary">Задачи сотрудника</h2>
      <p className="text-text-primary">
        Система анализирует данные судебных дел и формирует задачи для сотрудников 
        на основе проверки соблюдения процессуальных сроков. Выберите сотрудника из списка для просмотра его задач
        и нажмите кнопку "Найти задачи". Вы увидите таблицу всех задач, назначенных выбранному сотруднику
      </p>

      <div className="bg-white p-6 rounded-lg border border-border-default shadow-sm">
        <h3 className="font-semibold text-text-primary mb-4">Принцип работы системы задач</h3>
        
        <div className="space-y-4">
          <Step number={1} title="Анализ данных" description="Система анализирует данные из детального отчета и отчета по документам, определяет этапы дел и проверяет соблюдение сроков" />
          <Step number={2} title="Формирование задач" description="На основе проваленных проверок система создает задачи с конкретными формулировками и привязывает их к ответственным исполнителям" />
          <Step number={3} title="Группировка по исполнителям" description="Задачи можно сгруппировать по ответственным исполнителям, что позволяет каждому сотруднику видеть только свои задачи" />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-4 rounded-lg border border-border-default shadow-sm">
          <h4 className="font-semibold text-text-primary mb-3">Типы задач</h4>
          <ul className="space-y-2 text-sm text-text-secondary">
            <li className="flex items-start"><span className="text-green mr-2">•</span><span>Задачи искового производства</span></li>
            <li className="flex items-start"><span className="text-green mr-2">•</span><span>Задачи приказного производства</span></li>
            <li className="flex items-start"><span className="text-green mr-2">•</span><span>Задачи по работе с документами</span></li>
            <li className="flex items-start"><span className="text-green mr-2">•</span><span>Доп. задачи по контролю сроков</span></li>
          </ul>
        </div>

        <div className="bg-white p-4 rounded-lg border border-border-default shadow-sm">
          <h4 className="font-semibold text-text-primary mb-3">Источники данных</h4>
          <ul className="space-y-2 text-sm text-text-secondary">
            <li className="flex items-start"><span className="text-text-secondary mr-2">•</span><span>Детальный отчет по судебной работе</span></li>
            <li className="flex items-start"><span className="text-text-secondary mr-2">•</span><span>Отчет по полученным и переданным документам</span></li>
          </ul>
        </div>
      </div>

      <div className="bg-white p-4 rounded-lg border border-border-default">
        <h4 className="font-semibold text-text-primary mb-2">Содержимое задачи</h4>
        <div className="text-sm text-text-secondary space-y-2">
            <p>Каждая задача содержит:</p>
            <ul className="list-disc list-inside ml-4 space-y-1">
            <li><strong>Код задачи</strong> — уникальный идентификатор в системе</li>
            <li><strong>Код результата проверки</strong> — ссылка на проверку, вызвавшую задачу</li>
            <li><strong>Текст задачи</strong> — конкретное действие для выполнения</li>
            <li><strong>Причина постановки</strong> — обоснование формирования задачи</li>
            <li><strong>Дата создания</strong> — когда задача была сформирована</li>
            <li><strong>Статус выполнения</strong> — выполнена или нет</li>
            <li><strong>Фактическая дата выполнения</strong> — когда задача была закрыта</li>
            <li><strong>Кем создана</strong> — логин пользователя, запустившего анализ</li>
            <li><strong>Плановая дата исполнения</strong> — срок, к которому нужно выполнить (из проверки)</li>
            <li><strong>Ответственный исполнитель</strong> — сотрудник, назначенный на задачу</li>
            </ul>
        </div>
        </div>
    </div>
  );
}

function Step({ number, title, description }: { number: number; title: string; description: string }) {
  return (
    <div className="flex items-start">
      <div className="w-8 h-8 bg-bg-green-transparent rounded-full mr-4 mt-0.5 flex items-center justify-center flex-shrink-0">
        <span className="text-sm font-bold text-green-dark">{number}</span>
      </div>
      <div>
        <h4 className="font-semibold text-text-primary">{title}</h4>
        <p className="text-text-secondary text-sm mt-1">{description}</p>
      </div>
    </div>
  );
}


