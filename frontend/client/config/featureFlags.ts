// config/featureFlags.ts
export interface FeatureFlags {
  hasPreviousReport: boolean;
  enableComparison: boolean; 
}

// Временная конфигурация для тестирования
export const featureFlags: FeatureFlags = {
  hasPreviousReport: false, // Меняем на true/false для тестирования
  enableComparison: false   // Отключаем функционал сравнения
};