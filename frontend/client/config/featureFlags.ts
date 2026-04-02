// config/featureFlags.ts
export interface FeatureFlags {
  hasPreviousReport: boolean;
  enableComparison: boolean; 
}

// Временная конфигурация для тестирования
export const featureFlags: FeatureFlags = {
  hasPreviousReport: false, // Меняется на true/false для тестирования
  enableComparison: false   // Отключает функционал сравнения
};