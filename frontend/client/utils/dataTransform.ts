// src/utils/dataTransform.ts
import { 
  ChartItemConfig, 
  ChartGroupConfig, 
  stageNameToLabel,
  lawsuitChecksToLabel, 
  orderChecksToLabel,
  documentsChecksToLabel,
  lawsuitTermsV2Config,
  orderTermsV2Config, 
  documentsChartConfig
} from '@/config/chartConfig';

// Функция для преобразования данных радуги (числа -> объекты с метаданными)
export const transformRainbowData = (values: number[], config: ChartItemConfig[]) => {
  if (values.length !== config.length) {
    console.warn(`Длина данных с бэкенда (${values.length}) не совпадает с длиной конфига (${config.length}).`);
    const adjustedValues = [...values];
    while (adjustedValues.length < config.length) adjustedValues.push(0);
    adjustedValues.length = config.length;

    return config.map((item, index) => ({
      name: item.name,
      label: item.label,
      value: adjustedValues[index],
      color: item.color
    }));
  }

  return config.map((item, index) => ({
    name: item.name,
    label: item.label,
    value: values[index],
    color: item.color
  }));
};

// Функция для преобразования данных статусов (использует обновленный stageNameToLabel)
export const transformTermsData = (
  backendData: Array<{ group_name: string; values: number[] }>, 
  config: ChartGroupConfig[]
) => {
  return config.map((groupConfig) => {
    // Ищем данные по русскому названию через обновленный маппинг проверок
    const backendGroup = backendData.find(group => 
      stageNameToLabel[group.group_name] === groupConfig.title
    );
    
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

// Функция для v2 формата (использует специализированные маппинги)
export const transformTermsV2Data = (
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
export const transformLawsuitV2Data = (backendData: Array<{ group_name: string; values: number[] }>) => {
  return transformTermsV2Data(backendData, lawsuitTermsV2Config, lawsuitChecksToLabel);
};

export const transformOrderV2Data = (backendData: Array<{ group_name: string; values: number[] }>) => {
  return transformTermsV2Data(backendData, orderTermsV2Config, orderChecksToLabel);
};

export const transformDocumentsData = (backendData: Array<{ group_name: string; values: number[] }>) => {
  return transformTermsV2Data(backendData, documentsChartConfig, documentsChecksToLabel);
};