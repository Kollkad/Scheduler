import { useState } from "react";
import { PageContainer } from "@/components/PageContainer";
import { TabsContainer } from "@/components/TabsContainer";
import { RainbowMeanings } from "@/components/RainbowMeanings";
import { TermsOfSupportMeanings } from "@/components/TermsOfSupportMeanings";
import { featureFlags } from '@/config/featureFlags';

export function SystemOverview() {
  const tabs = [
    {
      id: 'introduction',
      label: 'Введение',
      content: (
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-gray-900">Планировщик судебных дел</h2>
          <p className="text-gray-700">
            Данная система предназначена для комплексного анализа и отслеживания судебных дел 
            банка. Инструмент позволяет визуализировать данные в различных разрезах и оперативно 
            реагировать на изменения сроков сопровождения дел.
          </p>
          
          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
            <h3 className="font-semibold text-blue-900 mb-2">Начало работы</h3>
            <p className="text-blue-800 text-sm">
              Для начала работы с системой необходимо:
            </p>
            <ol className="list-decimal list-inside ml-4 text-blue-800 text-sm space-y-1 mt-2">
              <li>Нажать кнопку "Загрузить файлы" в верхней части интерфейса</li>
              <li>Загрузить два обязательных файла в формате Excel:
                <ul className="list-disc list-inside ml-6">
                  <li>Текущий детальный отчет по судебной работе(.xlsx)</li>
                  <li>Отчёт по полученным и переданным документам(.xlsx)</li>
                </ul>
              </li>
            </ol>
          </div>

          <h3 className="font-semibold text-gray-900">Страницы системы:</h3>
          <ul className="list-disc list-inside text-gray-700 space-y-2">
            <li><span className="font-medium">Обзор системы</span> (текущая страница) - инструкция и описание возможностей</li>
            <li><span className="font-medium">Rainbow</span> - цветовая оценка сроков сопровождения дел</li>
            <li><span className="font-medium">Сроки сопровождения</span> - детальный анализ по этапам судебного процесса</li>
            <li><span className="font-medium">Задачи сотрудников</span> - выбрать задачи конкретного сотрудника по результатам анализа отчета</li>
          </ul>

          <h3 className="font-semibold text-gray-900">Обязательные столбцы в детальном отчете:</h3>
          <ul className="list-decimal list-inside text-gray-700 space-y-2">
            <p>Важные стобцы для очистки отчета:</p>
            <li>№ п/п - начальная точка выбора данных</li>
            <li>Итого - конечная точка</li>

            <p>О делах:</p>
            <li>ГОСБ</li>
            <li>Код дела</li>
            <li>Категория дела</li>
            <li>Статус дела</li>
            <li>Вид дела</li>
            <li>Способ судебной защиты</li>
            <li>Суд, рассматривающий дело</li>
            <li>Ответственный исполнитель</li>
            <li>Подразделение (ГОСБ)</li>
            <li>Комментарии</li>
            <li>Определение суда с реакцией на поданное заявление</li>
            
            <p>Даты:</p>
            <li>Дата подачи иска/заявления</li>
            <li>Дата предыдущего заседания суда</li>
            <li>Дата ближайшего заседания суда</li>
            <li>Дата вступления в законную силу решения суда / судебного приказа / судебного акта, завершающего производство в инстанции</li>
            <li>Дата получения решения суда / судебного приказа / судебного акта, завершающего производство в инстанции</li>
            <li>Дата закрытия дела</li>
            <li>Дата вынесения определения суда с реакцией на поданное заявление</li>
            <li>Дата последнего поступления запроса в ЮП</li>
            <li>Дата получения финального судебного акта</li>
            <li>Дата передачи финального акта в БП</li>
            <li>Фактическая дата передачи ИД</li>
          </ul>
          <h3 className="font-semibold text-gray-900">Обязательные столбцы в отчете по документам:</h3> 
          <ul className="list-decimal list-inside text-gray-700 space-y-2">
            <li>Код дела</li>
            <li>Документ</li>
            <li>Категория подразделения</li>
            <li>Дата получения</li>
            <li>Дата передачи</li>
            <li>Дата запроса</li>
            <li>Суть ответа</li>
            <li>Код запроса</li>
            <li>Суд, рассматривающий дело (название суда)</li>
          </ul>
        </div>
      )
    },
    {
      id: 'rainbow',
      label: 'Rainbow',
      content: (
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-gray-900">Цветовая система оценки (Rainbow)</h2>
          <p className="text-gray-700">
            Rainbow - это визуальная система оценки сроков сопровождения дел, где каждый цвет соответствует 
            определенному состоянию дела. Система позволяет быстро оценить общую ситуацию 
            и выявить проблемные зоны.
          </p>

          <RainbowMeanings />

          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
            <h3 className="font-semibold text-blue-900 mb-3">Возможности раздела Rainbow:</h3>
            <ul className="list-disc list-inside text-blue-800 text-sm space-y-2">
              <li>Нажмите на любой цветной столбец диаграммы для просмотра дел соответствующего статуса</li>
              <li>Используйте форму фильтров для детальной настройки отчета</li>
              <li>Анализируйте распределение дел по цветам для выявления проблемных зон</li>
              <li>Нажмите на строку в таблице для перехода к детальной информации о деле</li>
            </ul>
          </div>

          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-3">Условия определения цветов:</h3>
            
            <div className="text-sm text-gray-700 mb-4">
              <p className="font-medium mb-2">Общие условия:</p>
              <ul className="list-disc list-inside ml-4">
                <li>Только дела с категорией "Иск от Банка"</li>
                <li>Нет дел со статусом "Закрыто"</li>
                <li>Нет дел со статусом "Ошибка-Дубликат"</li>
                <li>Нет дел со статусом "Отозвано инициатором"</li>
              </ul>
            </div>

            <div className="space-y-4">
              <div className="flex items-start">
                <div className="w-4 h-4 bg-black rounded mr-3 mt-0.5 flex-shrink-0"></div>
                <div>
                  <p className="font-medium text-sm">Ипотечные кредиты (ИК)</p>
                  <p className="text-xs text-gray-600">Вид запроса содержит "залог"</p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="w-4 h-4 bg-gray-400 rounded mr-3 mt-0.5 flex-shrink-0"></div>
                <div>
                  <p className="font-medium text-sm">Серый</p>
                  <p className="text-xs text-gray-600">Статус дела = "Переоткрыто"</p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="w-4 h-4 bg-green-500 rounded mr-3 mt-0.5 flex-shrink-0"></div>
                <div>
                  <p className="font-medium text-sm">Зеленый</p>
                  <p className="text-xs text-gray-600">Статус дела = "Суд. акт вступил в законную силу" И заполнена "Фактическая дата передачи ИД"</p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="w-4 h-4 bg-yellow-400 rounded mr-3 mt-0.5 flex-shrink-0"></div>
                <div>
                  <p className="font-medium text-sm">Желтый</p>
                  <p className="text-xs text-gray-600">Статус дела = "Условно закрыто" И заполнена "Фактическая дата передачи ИД"</p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="w-4 h-4 bg-orange-500 rounded mr-3 mt-0.5 flex-shrink-0"></div>
                <div>
                  <p className="font-medium text-sm">Оранжевый</p>
                  <p className="text-xs text-gray-600">Статус дела = "Суд. акт вступил в законную силу" И НЕ заполнена "Фактическая дата передачи ИД"</p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="w-4 h-4 bg-blue-600 rounded mr-3 mt-0.5 flex-shrink-0"></div>
                <div>
                  <p className="font-medium text-sm">Синий</p>
                  <p className="text-xs text-gray-600">Способ судебной защиты = "Приказное производство" И "Дата последнего поступления запроса в ЮП" более 90 дней назад</p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="w-4 h-4 bg-red-500 rounded mr-3 mt-0.5 flex-shrink-0"></div>
                <div>
                  <p className="font-medium text-sm">Красный</p>
                  <p className="text-xs text-gray-600">"Дата последнего поступления запроса в ЮП" ранее 2023 года</p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="w-4 h-4 bg-purple-500 rounded mr-3 mt-0.5 flex-shrink-0"></div>
                <div>
                  <p className="font-medium text-sm">Лиловый</p>
                  <p className="text-xs text-gray-600">Способ судебной защиты = "Исковое производство" И "Дата последнего поступления запроса в ЮП" более 120 дней назад</p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="w-4 h-4 bg-white border border-gray-300 rounded mr-3 mt-0.5 flex-shrink-0"></div>
                <div>
                  <p className="font-medium text-sm">Белый</p>
                  <p className="text-xs text-gray-600">Все остальные дела, не подходящие под вышеперечисленные условия</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )
    },
    {
      id: 'terms',
      label: 'Сроки сопровождения',
      content: (
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-gray-900">Сроки сопровождения</h2>
          <p className="text-gray-700">
            Данный раздел предоставляет детальную информацию о движении дел по этапам 
            судебного процесса с проверкой соблюдения сроков на каждом этапе.
          </p>

          <TermsOfSupportMeanings />

          <h3 className="font-semibold text-gray-900">Выбор способа судебной защиты:</h3>
          <p className="text-gray-700 text-sm">
            В верхней части страницы расположены переключатели между типами производств
          </p>

          {/* Исковое производство */}
          <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
            <h3 className="font-semibold text-gray-900 mb-4 text-lg">Исковое производство</h3>
            
            <div className="space-y-4">
              <StageAccordion 
                title="0. Этап исключений"
                description="Дела с особыми статусами, не подлежащие стандартной проверке"
                checks={[
                  "Переоткрыто",
                  "Жалоба подана", 
                  "Ошибка-Дубликат",
                  "Отозвано инициатором"
                ]}
              />

              <StageAccordion
                title="1. Подготовка документов"
                description="Смена первоначального статуса дела"
                checks={[
                  "Статус 'Подготовка документов' должен смениться на иной. Срок: 14 календарных дней от даты подачи иска или аналогичной ей"
                ]}
              />
              
              <StageAccordion
                title="2. Ожидание реакции суда"
                description="Получение определения суда по поданным документам"
                checks={[
                  "Должна появиться 'Дата вынесения определения суда'. Срок: 7 рабочих дней от даты подачи иска или аналогичной ей"
                ]}
              />

              <StageAccordion
                title="3. На рассмотрении"
                description="Контроль процессуальных сроков судебного рассмотрения"
                checks={[
                  "Ближайшее СЗ назначено. Срок: 3 рабочих дня от даты вынесения определения суда",
                  "Интервал между заседаниями соответствует норме. Срок: не более 2 рабочих дней от даты предыдущего СЗ до даты ближайшего",
                  "Общий срок рассмотрения. Срок: 60 календарных дней от даты подачи иска или аналогичной ей"
                ]}
              />

              <StageAccordion
                title="4. Решение вынесено"
                description="Проверка сроков вынесения, получения и передачи решения суда"
                checks={[
                  "Решение вынесено. Срок: 45 календарных дней от даты вынесения решения суда до даты вступления в законную силу", //от DECISION_COURT_DATE до COURT_DECISION_DATE
                  "Решение получено. Срок: 3 календарных дня от даты вступления в законную силу до даты получения решения", // от COURT_DECISION_DATE до DECISION_RECEIPT_DATE
                  "Решение передано и отражена фактическая дата передачи ИД. Срок: за 1 календарный день от даты вступления в законную силу" //от COURT_DECISION_DATE, появится ACTUAL_TRANSFER_DATE
                ]}
              />

              <StageAccordion
                title="5. ИД получен"
                description="Проверка получения и передачи исполнительного листа по отчету полученных и переданных документов в ПСИП"
                checks={[
                  "Для записей из детального отчета берется подходящая запись из отчета документов",
                  "'Суть ответа' заполнена 'Передача подтверждена'. Срок: 14 календарных дней от даты запроса до дня проверки'"
                ]}
              />

              <StageAccordion
                title="6. Этап закрытия дела"
                description="Проверка своевременности закрытия дела"
                checks={[
                  "Дело закрыто вовремя. Срок: 125 календарных дней с даты подачи иска до даты закрытия дела"
                ]}
              />
            </div>
          </div>

          {/* Приказное производство */}
          <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
            <h3 className="font-semibold text-gray-900 mb-4 text-lg">Приказное производство</h3>
            
            <div className="space-y-4">
              <StageAccordion 
                title="0. Этап исключений"
                description="Дела с особыми статусами, не подлежащие стандартной проверке"
                checks={[
                  "Переоткрыто",
                  "Жалоба подана",
                  "Ошибка-Дубликат", 
                  "Отозвано инициатором"
                ]}
              />
              
              <StageAccordion
                title="1. Подготовка документов"
                description="Смена первоначального статуса дела"
                checks={[
                  "Статус 'Подготовка документов' должен смениться на иной. Срок: 14 календарных дней от даты подачи иска или аналогичной ей"
                ]}
              />
              <StageAccordion
                title="2. Ожидание реакции суда"
                description="Получение реакции суда по поданным документам"
                checks={[
                  "Проверка выполнения всех условий: вынесение судебного приказа, заполнение дат получения/передачи ИД, статус 'Условно закрыто'. Срок: 60 календарных дней от даты подачи заявления или аналогичной ей до даты проверки"
                  // COURT_DETERMINATION == COURT_ORDER
                  // ACTUAL_RECEIPT_DATE != ""
                  // ACTUAL_TRANSFER_DATE != ""
                  // CASE_STATUS == CONDITIONALLY_CLOSED
                ]}
              /> 
              
              <StageAccordion
                title="3. ИД получен"
                description="Проверка получения и передачи исполнительного листа по отчету полученных и переданных документов в ПСИП"
                checks={[
                  "Для записей из детального отчета берется подходящая запись из отчета документов",
                  "'Суть ответа' заполнена 'Передача подтверждена'. Срок: 14 календарных дней от даты запроса до дня проверки'"
                ]}
              />

              <StageAccordion
                title="4. Этап закрытия дела"
                description="Проверка своевременности закрытия дела"
                checks={[
                  "Дело закрыто вовремя. Срок: 90 календарных дней с даты подачи иска до даты закрытия дела"
                ]}
              />
            </div>

            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-semibold text-gray-900 mb-2">Особенности приказного производства:</h4>
              <ul className="list-disc list-inside text-gray-700 text-sm space-y-1">
                <li>Упрощенная процедура без судебных заседаний</li>
                <li>Сокращенные сроки рассмотрения по сравнению с исковым производством</li>
                <li>Основной результат - получение судебного приказа</li>
                <li>Автоматическая проверка всех условий реакции суда одновременно</li>
              </ul>
            </div>
          </div>

          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
            <h4 className="font-semibold text-blue-900 mb-2">Принцип работы системы:</h4>
            <ul className="list-disc list-inside text-blue-800 text-sm space-y-1">
              <li>Каждое дело автоматически определяется в соответствующий этап</li>
              <li>На каждом этапе выполняются проверки соблюдения сроков</li>
              <li>Результаты проверок объединяются в комбинированные статусы</li>
              <li>Система учитывает иерархию этапов от исключений к стандартным этапам</li>
              <li>Для каждого типа производства (исковое/приказное) применяются свои этапы и проверки</li>
            </ul>
          </div>
        </div>
      )
    },
    ...(featureFlags.enableComparison ? [{
      id: 'comparison',
      label: 'Сравнение периодов',
      content: (
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-gray-900">Сравнение периодов</h2>
          <p className="text-gray-700">
            Данный раздел позволяет анализировать динамику показателей между текущим 
            и предыдущим отчетным периодом.
          </p>

          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
            <h3 className="font-semibold text-blue-900 mb-2">Возможности раздела:</h3>
            <ul className="list-disc list-inside text-blue-800 text-sm space-y-2">
              <li>Сравнение количества дел по цветам между периодами</li>
              <li>Анализ динамики сроков сопровождения</li>
              <li>Отслеживание изменений в эффективности работы</li>
              <li>Выявление тенденций и проблемных зон</li>
            </ul>
          </div>

          <h3 className="font-semibold text-gray-900">Как работает сравнение:</h3>
          <ol className="list-decimal list-inside text-gray-700 space-y-2">
            <li>Загрузите текущий отчетный период</li>
            <li>Загрузите отчет за предыдущий период (опционально)</li>
            <li>Система автоматически сопоставит данные по идентификаторам дел</li>
            <li>Получите наглядную визуализацию изменений</li>
          </ol>
        </div>
      )
    }] : []),
    {
  id: 'employee-tasks',
  label: 'Задачи сотрудника',
  content: (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">Задачи сотрудника</h2>
      <p className="text-gray-700">
        Система анализирует данные судебных дел и формирует задачи для сотрудников 
        на основе проверки соблюдения процессуальных сроков. Выберите сотрудника из списка для просмотра его задач
        и нажмите кнопку "Найти задачи". Вы увидите таблицу всех задач, назначенных выбранному сотруднику
      </p>

      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
        <h3 className="font-semibold text-gray-900 mb-4">Принцип работы системы задач</h3>
        
        <div className="space-y-4">
          <div className="flex items-start">
            <div className="w-8 h-8 bg-blue-100 rounded-full mr-4 mt-0.5 flex items-center justify-center flex-shrink-0">
              <span className="text-sm font-bold text-blue-800">1</span>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900">Анализ данных</h4>
              <p className="text-gray-700 text-sm mt-1">
                Система анализирует данные из детального отчета и отчета по документам, 
                определяет этапы дел и проверяет соблюдение сроков
              </p>
            </div>
          </div>

          <div className="flex items-start">
            <div className="w-8 h-8 bg-green-100 rounded-full mr-4 mt-0.5 flex items-center justify-center flex-shrink-0">
              <span className="text-sm font-bold text-green-800">2</span>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900">Формирование задач</h4>
              <p className="text-gray-700 text-sm mt-1">
                На основе проваленных проверок система создает задачи с конкретными формулировками 
                и привязывает их к ответственным исполнителям
              </p>
            </div>
          </div>

          <div className="flex items-start">
            <div className="w-8 h-8 bg-purple-100 rounded-full mr-4 mt-0.5 flex items-center justify-center flex-shrink-0">
              <span className="text-sm font-bold text-purple-800">3</span>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900">Группировка по исполнителям</h4>
              <p className="text-gray-700 text-sm mt-1">
                Задачи можно сгруппировать по ответственным исполнителям, 
                что позволяет каждому сотруднику видеть только свои задачи
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <h4 className="font-semibold text-gray-900 mb-3">Типы задач</h4>
          <ul className="space-y-2 text-sm text-gray-700">
            <li className="flex items-start">
              <span className="text-blue-600 mr-2">•</span>
              <span>Задачи искового производства</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-600 mr-2">•</span>
              <span>Задачи приказного производства</span>
            </li>
            <li className="flex items-start">
              <span className="text-purple-600 mr-2">•</span>
              <span>Задачи по работе с документами</span>
            </li>
            <li className="flex items-start">
              <span className="text-orange-600 mr-2">•</span>
              <span>Доп. задачи по контролю сроков</span>
            </li>
          </ul>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <h4 className="font-semibold text-gray-900 mb-3">Источники данных</h4>
          <ul className="space-y-2 text-sm text-gray-700">
            <li className="flex items-start">
              <span className="text-gray-600 mr-2">•</span>
              <span>Детальный отчет по судебной работе</span>
            </li>
            <li className="flex items-start">
              <span className="text-gray-600 mr-2">•</span>
              <span>Отчет по полученным и переданным документам</span>
            </li>
            <li className="flex items-start">
              <span className="text-gray-600 mr-2">•</span>
              <span>Данные мониторинга этапов производства</span>
            </li>
          </ul>
        </div>
      </div>

      <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
        <h4 className="font-semibold text-gray-900 mb-2">Формат задачи</h4>
        <div className="text-sm text-gray-700 space-y-2">
          <p>Каждая задача содержит:</p>
          <ul className="list-disc list-inside ml-4 space-y-1">
            <li><strong>Уникальный код задачи</strong> - идентификатор в системе</li>
            <li><strong>Тип задачи</strong> - категория (исковое, приказное, документы)</li>
            <li><strong>Код дела</strong> - привязка к конкретному судебному делу</li>
            <li><strong>Текст задачи</strong> - конкретное действие для выполнения</li>
            <li><strong>Причина</strong> - обоснование формирования задачи</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
  ];

  return (
    <PageContainer>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Планировщик судебных дел</h1>
        <p className="text-gray-600">Инструкция по работе с системой мониторинга судебных дел</p>
      </div>

      <TabsContainer tabs={tabs} defaultTab="introduction" />
    </PageContainer>
  );
}
const StageAccordion = ({ title, description, checks }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border border-gray-200 rounded-lg">
      <button
        className="w-full px-4 py-3 text-left flex justify-between items-center hover:bg-gray-50 transition-colors"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div>
          <h4 className="font-semibold text-gray-900">{title}</h4>
          <p className="text-sm text-gray-600 mt-1">{description}</p>
        </div>
        <svg 
          className={`w-5 h-5 text-gray-500 transform transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      
      {isOpen && (
        <div className="px-4 pb-3">
          <ul className="list-disc list-inside text-sm text-gray-700 space-y-2 mt-2">
            {checks.map((check, index) => (
              <li key={index}>{check}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};