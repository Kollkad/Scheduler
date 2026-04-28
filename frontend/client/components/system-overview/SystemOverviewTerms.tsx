// frontend/client/components/system-overview/SystemOverviewTerms.tsx

import { useState, useEffect } from "react";
import { Loader } from "lucide-react";
import { apiClient } from "@/services/api/client";
import { API_ENDPOINTS } from "@/services/api/endpoints";
import { SystemOverviewStageAccordion } from "@/components/system-overview/SystemOverviewStageAccordion";

interface CheckInfo {
  checkCode: string;
  checkName: string;
}

interface StageInfo {
  stageCode: string;
  stageName: string;
  checks: CheckInfo[];
}

interface StagesResponse {
  success: boolean;
  stages: StageInfo[];
  message: string;
}

//TODO: добавить описания для проверок в модель данных и использовать в обзоре системы на frontend/client/components/system-overview/SystemOverviewTerms.tsx
// Временный справочник описаний проверок (заглушка)
const CHECK_DESCRIPTIONS: Record<string, string> = {
  "exceptionsL": "Дела с особыми статусами, не подлежащие стандартной проверке: Переоткрыто, Жалоба подана, Ошибка-Дубликат, Отозвано инициатором",
  "exceptionsO": "Дела с особыми статусами, не подлежащие стандартной проверке: Переоткрыто, Жалоба подана, Ошибка-Дубликат, Отозвано инициатором",
  "firstStatusChangedL": "Статус 'Подготовка документов' должен смениться на иной. Срок: 14 календарных дней от даты подачи иска или аналогичной ей",
  "firstStatusChangedO": "Статус 'Подготовка документов' должен смениться на иной. Срок: 14 календарных дней от даты подачи иска или аналогичной ей",
  "courtReactionL": "Должна появиться 'Дата вынесения определения суда'. Срок: 7 рабочих дней от даты подачи иска или аналогичной ей",
  "courtReactionO": "Проверка выполнения всех условий: вынесение судебного приказа, заполнение дат получения/передачи ИД, статус 'Условно закрыто'. Срок: 60 календарных дней от даты подачи заявления или аналогичной ей до даты проверки",
  "nextHearingPresentL": "Ближайшее СЗ назначено. Срок: 3 рабочих дня от даты вынесения определения суда",
  "hearingIntervalL": "Интервал между заседаниями соответствует норме. Срок: не более 2 рабочих дней от даты предыдущего СЗ до даты ближайшего",
  "consideration60daysL": "Общий срок рассмотрения. Срок: 60 календарных дней от даты подачи иска или аналогичной ей",
  "decisionDateL": "Решение вынесено. Срок: 45 календарных дней от даты вынесения решения суда до даты вступления в законную силу",
  "decisionReceiptL": "Решение получено. Срок: 3 календарных дня от даты вступления в законную силу до даты получения решения",
  "decisionTransferL": "Решение передано и отражена фактическая дата передачи ИД. Срок: за 1 календарный день от даты вступления в законную силу",
  "executionDocumentReceivedL": "Для записей из детального отчета берется подходящая запись из отчета документов. 'Суть ответа' заполнена 'Передача подтверждена'. Срок: 14 календарных дней от даты запроса до дня проверки",
  "executionDocumentReceivedO": "Для записей из детального отчета берется подходящая запись из отчета документов. 'Суть ответа' заполнена 'Передача подтверждена'. Срок: 14 календарных дней от даты запроса до дня проверки",
  "closedL": "Дело закрыто вовремя. Срок: 125 календарных дней с даты подачи иска до даты закрытия дела",
  "closedO": "Дело закрыто вовремя. Срок: 90 календарных дней с даты подачи иска до даты закрытия дела",
};

// Выносит этапы-исключения на 0 позицию, остальные сохраняют порядок
const sortStagesWithExceptionsFirst = (stages: StageInfo[]): StageInfo[] => {
  return [...stages].sort((a, b) => {
    if (a.stageCode.includes("exceptions")) return -1;
    if (b.stageCode.includes("exceptions")) return 1;
    return 0;
  });
};

export function SystemOverviewTerms() {
  const [lawsuitStages, setLawsuitStages] = useState<StageInfo[]>([]);
  const [orderStages, setOrderStages] = useState<StageInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadStages = async () => {
      try {
        const [lawsuitRes, orderRes] = await Promise.all([
          apiClient.get<StagesResponse>(`${API_ENDPOINTS.CASE_STAGES_WITH_CHECKS}/lawsuit/with-checks`),
          apiClient.get<StagesResponse>(`${API_ENDPOINTS.CASE_STAGES_WITH_CHECKS}/order/with-checks`),
        ]);

        if (lawsuitRes.success) setLawsuitStages(lawsuitRes.stages);
        if (orderRes.success) setOrderStages(orderRes.stages);
      } catch (e) {
        console.error("Ошибка загрузки этапов:", e);
      } finally {
        setLoading(false);
      }
    };

    loadStages();
  }, []);

  // Формирование списка проверок для этапа
  const getChecksList = (stage: StageInfo): string[] => {
    return stage.checks.map(check => {
      const description = CHECK_DESCRIPTIONS[check.checkCode] || "";
      if (description) {
        return `${check.checkName} — ${description}`;
      }
      return check.checkName;
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Loader className="h-6 w-6 animate-spin text-blue" />
      </div>
    );
  }

  const sortedLawsuitStages = sortStagesWithExceptionsFirst(lawsuitStages);
  const sortedOrderStages = sortStagesWithExceptionsFirst(orderStages);

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-text-primary">Сроки сопровождения</h2>
      <p className="text-text-primary">
        Данный раздел предоставляет детальную информацию о движении дел по этапам 
        судебного процесса с проверкой соблюдения сроков на каждом этапе.
      </p>

      {/* Принцип работы системы */}
      <div className="bg-bg-light-green p-4 rounded-lg border border-green-dark">
        <h3 className="font-semibold text-green-dark mb-2">Принцип работы модуля:</h3>
        <ul className="list-disc list-inside text-green-dark text-sm space-y-1">
          <li>Каждое дело автоматически определяется в соответствующий этап</li>
          <li>Для каждого типа производства (исковое/приказное) применяются свои этапы и проверки</li>
          <li>На каждом этапе выполняются проверки соблюдения сроков исполнения на выполнение определенных действий</li>
          <li>Результаты проверок сроков используются в модуле задач</li>
        </ul>
      </div>

      {/* Работа со страницей */}
      <div>
        <h3 className="font-semibold text-text-primary">Работа со страницей</h3>
        <p className="text-text-secondary text-sm mt-1">
          Выбор способа судебной защиты для просмотра сроков осуществляется в верхней части страницы 
          с помощью чекбоксов. Тип производства влияет на количество проверок дела и соответственно 
          на график проверок. Ниже представлены описания этапов и проверок системы.
        </p>
      </div>

      {/* Исковое производство */}
      <div className="bg-white p-6 rounded-lg border border-border-default shadow-sm">
        <h3 className="font-semibold text-text-primary mb-4 text-lg">Исковое производство</h3>
        
        <div className="space-y-4">
          {sortedLawsuitStages.map((stage, index) => (
            <SystemOverviewStageAccordion
              key={stage.stageCode}
              title={`${index}. ${stage.stageName}`}
              checks={getChecksList(stage)}
            />
          ))}
        </div>
      </div>

      {/* Приказное производство */}
      <div className="bg-white p-6 rounded-lg border border-border-default shadow-sm">
        <h3 className="font-semibold text-text-primary mb-4 text-lg">Приказное производство</h3>
        
        <div className="space-y-4">
          {sortedOrderStages.map((stage, index) => (
            <SystemOverviewStageAccordion
              key={stage.stageCode}
              title={`${index}. ${stage.stageName}`}
              checks={getChecksList(stage)}
            />
          ))}
        </div>

        <div className="mt-6 p-4 bg-bg-default-light-field rounded-lg">
          <h4 className="font-semibold text-text-primary mb-2">Особенности приказного производства:</h4>
          <ul className="list-disc list-inside text-text-secondary text-sm space-y-1">
            <li>Упрощенная процедура без судебных заседаний</li>
            <li>Сокращенные сроки рассмотрения по сравнению с исковым производством</li>
            <li>Основной результат - получение судебного приказа</li>
            <li>Автоматическая проверка всех условий реакции суда одновременно</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
