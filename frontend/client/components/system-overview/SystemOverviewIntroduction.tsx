// frontend/client/components/system-overview/SystemOverviewIntroduction.tsx

import { useState, useEffect } from "react";
import { ChevronRight } from "lucide-react";
import { apiClient } from "@/services/api/client";
import { API_ENDPOINTS } from "@/services/api/endpoints";

interface DocFile {
  filename: string;
  name: string;
}

interface DocsListResponse {
  success: boolean;
  files: DocFile[];
  message: string;
}

export function SystemOverviewIntroduction() {
  const [docs, setDocs] = useState<DocFile[]>([]);

  useEffect(() => {
    apiClient.get<DocsListResponse>(API_ENDPOINTS.DOCS_LIST)
      .then(data => {
        if (data.success) setDocs(data.files);
      })
      .catch(() => {});
  }, []);

  const handleOpenDoc = (filename: string) => {
    window.open(`${API_ENDPOINTS.DOCS_FILE}/${filename}`, '_blank');
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-text-primary">Введение</h2>
      <p className="text-text-primary">
        Система предназначена для комплексного анализа и отслеживания судебных дел банка. 
        На основе загруженных отчётов выполняются проверки сроков по этапам судебного процесса, 
        формируются задачи для сотрудников и цветовая оценка состояния дел. Результаты анализа 
        можно выгружать в сетевую папку для совместной работы — сотрудники отмечают выполнение 
        задач, руководитель собирает ответы и контролирует исполнение.
      </p>
      
      <div className="bg-bg-light-green p-4 rounded-lg border border-green-dark">
        <h3 className="font-semibold text-green-dark mb-2">Начало работы</h3>
        <p className="text-green-dark text-sm">
          Для получения всех актуальных данных необходимо:
        </p>
        <ol className="list-decimal list-inside ml-4 text-green-dark text-sm space-y-1 mt-2">
          <li>Нажать кнопку "Обновить данные" в верхней части интерфейса</li>
          <li>Поставить отметки в чек-боксах:
            <ul className="list-disc list-inside ml-6">
              <li>Загрузить данные анализа</li>
              <li>Загрузить ответы на задачи</li>
            </ul>
          </li>
        </ol>
      </div>

      <h3 className="font-semibold text-text-primary">Основные страницы системы:</h3>
      <ul className="list-disc list-inside text-text-secondary space-y-2">
        <li><span className="font-medium">Обзор системы</span> (текущая страница) — инструкция и описание возможностей</li>
        <li><span className="font-medium">Rainbow</span> — цветовая оценка сроков сопровождения дел</li>
        <li><span className="font-medium">Сроки сопровождения</span> — детальный анализ по этапам судебного процесса</li>
        <li><span className="font-medium">Задачи сотрудников</span> — выбрать задачи конкретного сотрудника по результатам анализа отчета</li>
        <li><span className="font-medium">Профиль пользователя</span> — личные задачи, репорты и статистика</li>
      </ul>

      {/* Частые вопросы */}
      <div>
        <h2 className="text-xl font-bold text-text-primary mb-3">Частые вопросы и необходимые инструкции</h2>
        {docs.length > 0 ? (
          <ul className="space-y-2">
            {docs.map((doc) => (
              <li key={doc.filename}>
                <button
                    onClick={() => handleOpenDoc(doc.filename)}
                    title="Ответ откроется в новой вкладке"
                    className="flex items-center gap-2 text-text-secondary hover:text-blue transition-colors group"
                    >
                    <ChevronRight className="h-5 w-5 text-green flex-shrink-0 group-hover:translate-x-0.5 transition-transform" />
                    <span className="text-base">{doc.name}</span>
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-text-secondary">Инструкции пока не добавлены</p>
        )}
      </div>

      {/* Обязательные данные */}
      <div>
        <h3 className="font-semibold text-text-primary mb-3">Обязательные данные</h3>
        <div className="space-y-3">
          <CollapsibleSection title="Обязательные столбцы в детальном отчете">
            <ul className="list-decimal list-inside text-text-secondary space-y-2">
              <p>Важные столбцы для очистки отчета:</p>
              <li>№ п/п — начальная точка выбора данных</li>
              <li>Итого — конечная точка</li>

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
          </CollapsibleSection>

          <CollapsibleSection title="Обязательные столбцы в отчете по документам">
            <ul className="list-decimal list-inside text-text-secondary space-y-2">
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
          </CollapsibleSection>
        </div>
      </div>
    </div>
  );
}

// Раскрывающаяся секция для списков
function CollapsibleSection({ title, children }: { title: string; children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border border-border-default rounded-lg">
      <button
        className="w-full px-4 py-3 text-left flex justify-between items-center hover:bg-bg-default-light-field transition-colors"
        onClick={() => setIsOpen(!isOpen)}
      >
        <h3 className="font-semibold text-text-primary">{title}</h3>
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
          {children}
        </div>
      )}
    </div>
  );
}
