// frontend/client/config/sorterConfig.ts
import { SorterField } from '@/components/sorter/SorterTypes';

export const sorterConfig = {
  rainbow: {
    title: "Настройка отчета",
    fields: [
      {
        id: 'gosb',
        placeholder: 'ГОСБ',
        hasSearch: true,
        options: [],
        endpoint: 'gosb'
      },
      {
        id: 'courtProtectionMethod',
        placeholder: 'Способ судебной защиты', 
        hasSearch: false,
        options: [],
        endpoint: 'courtProtectionMethod'
      },
      {
        id: 'responsibleExecutor',
        placeholder: 'Ответственный исполнитель',
        hasSearch: true,
        options: [],
        endpoint: 'responsibleExecutor'
      },
      {
        id: 'currentPeriodColor', 
        placeholder: 'Цвет (текущий период)',
        hasSearch: false,
        options: [],
        endpoint: 'currentPeriodColor'
      },
      {
        id: 'courtReviewingCase',
        placeholder: 'Суд, рассматривающий дело',
        hasSearch: true, 
        options: [],
        endpoint: 'courtReviewingCase'
      }
    ] as SorterField[]
  }
};

export const getSorterConfig = (page: keyof typeof sorterConfig) => {
  return sorterConfig[page];
};


// Тип для удобства использования
export type SorterPage = keyof typeof sorterConfig;