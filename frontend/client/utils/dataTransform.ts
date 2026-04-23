// client/utils/dataTransform.ts
import { 
  ChartItemConfig, 
  ChartGroupConfig, 
  lawsuitChecksToLabel, 
  orderChecksToLabel,
  lawsuitTermsConfig,
  orderTermsConfig, 
  DEFAULT_SEGMENTS 
} from '@/config/chartConfig';

// Функция для преобразования данных радуги (числа -> объекты с метаданными)
export const transformRainbowData = (
  values: number[], 
  config: ChartItemConfig[],
  colorLabels?: string[]
) => {
  if (values.length !== config.length) {
    console.warn(`Длина данных с бэкенда (${values.length}) не совпадает с длиной конфига (${config.length}).`);
    const adjustedValues = [...values];
    while (adjustedValues.length < config.length) adjustedValues.push(0);
    adjustedValues.length = config.length;

    // Используются переданные метки цветов или дефолтные из конфига
    return config.map((item, index) => ({
      name: item.name,
      label: colorLabels?.[index] || item.label || item.name,
      value: adjustedValues[index],
      color: item.color
    }));
  }

  // Если все в порядке, ставятся переданные метки или дефолтные
  return config.map((item, index) => ({
    name: item.name,
    label: colorLabels?.[index] || item.label || item.name,
    value: values[index],
    color: item.color
  }));
};

// Функция для преобразования данных диаграмм производств (исковое/приказное)
// Сопоставляет данные с бэкенда (group_name = checkCode) с конфигом диаграммы
// и формирует структуру для SegmentedChart
export const transformTermsData = (
  backendData: Array<{ group_name: string; values: number[] }>, 
  config: ChartGroupConfig[],
  stageMapping: Record<string, string> 
) => {
  return config.map((groupConfig) => {
    const backendGroup = backendData.find(group => {
      const russianLabel = stageMapping[group.group_name];
      return russianLabel === groupConfig.title;
    });
    
    const segments = groupConfig.items.map((itemConfig, itemIndex) => {
      const value = backendGroup?.values?.[itemIndex] ?? 0;
      return {
        ...itemConfig,
        value: value
      };
    });

    return {
      title: groupConfig.title,
      segments: segments,
      total: segments.reduce((sum, segment) => sum + segment.value, 0)
    };
  });
};

// Специализированные функции для каждого модуля
export const transformLawsuitData = (backendData: Array<{ group_name: string; values: number[] }>) => {
  return transformTermsData(backendData, lawsuitTermsConfig, lawsuitChecksToLabel);
};

export const transformOrderData = (backendData: Array<{ group_name: string; values: number[] }>) => {
  return transformTermsData(backendData, orderTermsConfig, orderChecksToLabel);
};

export const transformDocumentsData = (
  backendData: Array<{ group_name: string; values: number[] }>
) => {
  if (!backendData || backendData.length === 0) {
    return [];
  }

  return backendData.map((group) => {
    const segments = DEFAULT_SEGMENTS.map((statusConfig, index) => ({
      ...statusConfig,
      value: group.values[index] ?? 0
    }));

    const total = segments.reduce((sum, seg) => sum + seg.value, 0);

    return {
      title: group.group_name,
      segments,
      total
    };
  });
};