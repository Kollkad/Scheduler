// services/api/endpoints.ts
export const API_ENDPOINTS = {
  // ==================== RAINBOW ====================
  RAINBOW_ANALYZE: '/api/rainbow/analyze',
  RAINBOW_CASES_BY_COLOR: '/api/rainbow/cases-by-color',
  RAINBOW_QUICK_TEST: '/api/rainbow/quick-test',
  RAINBOW_FILL_DIAGRAM: '/api/rainbow/fill-diagram',

  // ==================== DOCUMENTS ====================
  DOCUMENTS_ANALYZE: '/api/documents/analyze_documents',
  DOCUMENTS_FILTER: '/api/documents/filter_documents',
  DOCUMENTS_STATUSES: '/api/documents/document_statuses',
  DOCUMENTS_CHARTS: '/api/documents/analyze_document_charts', 
  DOCUMENT_DETAILS: '/api/documents/document',

  // ==================== TERMS V2 - LAWSUIT ====================
  TERMS_V2_LAWSUIT_ANALYZE: '/api/terms/v2/lawsuit/analyze_lawsuit',
  TERMS_V2_LAWSUIT_CHARTS: '/api/terms/v2/lawsuit/analyze_lawsuit_charts',
  TERMS_V2_LAWSUIT_FILTERED: '/api/terms/v2/lawsuit/filtered-cases',

  // ==================== TERMS V2 - ORDER ====================
  TERMS_V2_ORDER_ANALYZE: '/api/terms/v2/order/analyze_order',
  TERMS_V2_ORDER_CHARTS: '/api/terms/v2/order/analyze_order_charts',
  TERMS_V2_ORDER_FILTERED: '/api/terms/v2/order/filtered-cases',

  // ==================== TASKS ====================
  TASKS_CALCULATE: '/api/tasks/calculate',
  TASKS_LIST: '/api/tasks/list',
  TASKS_SAVE: '/api/tasks/save-all',
  TASKS_FILTER: '/api/tasks/filter',
  TASK_DETAILS: '/api/tasks',

  // ==================== FILE OPERATIONS ====================
  UPLOAD_FILE: '/upload-file',
  FILES_STATUS: '/files-status',
  REMOVE_FILE: '/remove-file',

  // ==================== TABLE SORTER & FILTERS ====================
  UNIQUE_VALUES: '/api/table-sorter/unique-values',
  FILTER_OPTIONS: '/api/filter-options',
  FILTERS_METADATA: '/api/filters/metadata',
  APPLY_FILTERS: '/api/filter/apply',

  // ==================== CASE DETAILS ====================
  CASE_DETAILS: '/api/case',
  FILTERED_CASES: '/api/terms/filtered-cases',

  // ==================== SAVING ENDPOINTS ====================
  SAVE_DETAILED_REPORT: '/api/save/detailed-report',
  SAVE_DOCUMENTS_REPORT: '/api/save/documents-report',
  SAVE_TERMS_PRODUCTIONS: '/api/save/terms-productions',
  SAVE_DOCUMENTS_ANALYSIS: '/api/save/documents-analysis',
  SAVE_TASKS: '/api/save/tasks',
  SAVE_RAINBOW_ANALYSIS: '/api/save/rainbow-analysis',
  SAVE_ALL_ANALYSIS: '/api/save/all-analysis',
  SAVE_AVAILABLE_DATA_STATUS: '/api/save/available-data',
  SAVE_ALL_PROCESSED_DATA_STATUS: '/api/save/all-processed-data',

  // ==================== RESET ====================
  RESET_ANALYSIS: '/reset-analysis',

  // ==================== УСТАРЕВШИЕ (НЕ ИСПОЛЬЗОВАТЬ) ====================
  // TERMS_LAWSUIT_ANALYZE: '/api/terms/lawsuit/analyze_l', // УСТАРЕЛО - использовать TERMS_V2_LAWSUIT_ANALYZE
  // TERMS_ORDER_ANALYZE: '/api/terms/order/analyze_o', // УСТАРЕЛО - использовать TERMS_V2_ORDER_ANALYZE
  // TERMS_LAWSUIT_TEST: '/api/terms/lawsuit/quick-test', // УСТАРЕЛО
  // TERMS_ORDER_TEST: '/api/terms/order/quick-test', // УСТАРЕЛО
  // FILTERED_LAWSUIT_CASES: '/api/terms/lawsuit/filtered-cases', // УСТАРЕЛО - использовать TERMS_V2_LAWSUIT_FILTERED
  // FILTERED_ORDER_CASES: '/api/terms/order/filtered-cases', // УСТАРЕЛО - использовать TERMS_V2_ORDER_FILTERED
} as const;