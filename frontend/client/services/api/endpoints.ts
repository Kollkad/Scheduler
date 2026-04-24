// client/services/api/endpoints.ts
export const API_ENDPOINTS = {
  // ==================== ACCESS ====================
  AUTH_STATUS: '/api/auth/status',
  AUTH_LOGIN: '/api/auth/login',
  AUTH_LOGOUT: '/api/auth/logout',
  USER_INFO: '/api/auth/user-info',
  
  // ==================== SEARCH ====================
  SEARCH_CASES: '/api/search/cases',

  // ==================== DATA EXCHANGE ====================
  EXCHANGE_INFO: '/api/exchange/info',
  EXCHANGE_EXPORT_ALL: '/api/exchange/export/all',
  EXCHANGE_EXPORT_OVERRIDES: '/api/exchange/export/user-overrides',
  EXCHANGE_EXPORT_MY_OVERRIDES: '/api/exchange/export/my-overrides',
  EXCHANGE_IMPORT_ALL: '/api/exchange/import/all',
  EXCHANGE_IMPORT_OVERRIDES: '/api/exchange/import/user-overrides',
  EXCHANGE_CLEAR: '/api/exchange/clear-app-data',
  
  // ==================== RAINBOW ====================
  RAINBOW_ANALYZE: '/api/rainbow/analyze',
  RAINBOW_CASES_BY_COLOR: '/api/rainbow/cases-by-color',
  RAINBOW_QUICK_TEST: '/api/rainbow/quick-test',
  RAINBOW_FILL_DIAGRAM: '/api/rainbow/fill-diagram',

  // ==================== DOCUMENTS V3 ====================
  DOCUMENTS_ANALYZE: '/api/documents/v3/analyze_documents',
  DOCUMENTS_FILTER: '/api/documents/v3/filter_documents',
  DOCUMENTS_STATUSES: '/api/documents/v3/document_statuses',
  DOCUMENTS_CHARTS: '/api/documents/v3/analyze_document_charts',
  DOCUMENT_DETAILS: '/api/documents/v3/document',

  // ==================== TERMS V3 - LAWSUIT ====================
  TERMS_LAWSUIT_ANALYZE: '/api/terms/v3/lawsuit/analyze_lawsuit',
  TERMS_LAWSUIT_CHARTS: '/api/terms/v3/lawsuit/analyze_lawsuit_charts',
  TERMS_LAWSUIT_FILTERED: '/api/terms/v3/lawsuit/filtered-cases',

  // ==================== TERMS V3 - ORDER ====================
  TERMS_ORDER_ANALYZE: '/api/terms/v3/order/analyze_order',
  TERMS_ORDER_CHARTS: '/api/terms/v3/order/analyze_order_charts',
  TERMS_ORDER_FILTERED: '/api/terms/v3/order/filtered-cases',

  // ==================== TASKS ====================
  TASKS_CALCULATE: '/api/tasks/calculate',
  TASKS_LIST: '/api/tasks/list',
  TASKS_SAVE: '/api/tasks/save-all',
  TASKS_STATUS: '/api/tasks/status',
  TASK_DETAILS: '/api/tasks',

  TASK_UPDATE: '/api/tasks',                      // PATCH /api/tasks/{taskCode}
  TASK_DELETE_OVERRIDE: '/api/tasks',             // DELETE /api/tasks/{taskCode}/override
  TASK_SHIFT_REASONS: '/api/tasks',               // GET /api/tasks/{taskCode}/shift-reasons

  // ==================== FILE OPERATIONS ====================
  UPLOAD_FILE: '/api/data/upload-file',
  FILES_STATUS: '/api/data/files-status',
  FILE_STATUS: '/api/data/file-status',
  REMOVE_FILE: '/api/data/remove-file',

  // ==================== TABLE SORTER & FILTERS ====================
  UNIQUE_VALUES: '/api/table-sorter/unique-values',
  FILTER_OPTIONS: '/api/filter-options',
  FILTERS_METADATA: '/api/filters/metadata',
  APPLY_FILTERS: '/api/filter/apply',

  // ==================== CASE DETAILS ====================
  CASE_DETAILS: '/api/case',
  FILTERED_CASES: '/api/terms/v3/lawsuit/filtered-cases',

  // ==================== SAVING ENDPOINTS ====================
  SAVE_DETAILED_REPORT: '/api/save/detailed-report',
  SAVE_DOCUMENTS_REPORT: '/api/save/documents-report',
  SAVE_STAGES: '/api/save/stages',
  SAVE_CHECKS: '/api/save/checks',
  SAVE_CHECK_RESULTS_CASES: '/api/save/check-results/cases',
  SAVE_CHECK_RESULTS_DOCUMENTS: '/api/save/check-results/documents',
  SAVE_TASKS: '/api/save/tasks',
  SAVE_TASKS_BY_EXECUTOR: '/api/save/tasks-by-executor',
  SAVE_USER_OVERRIDES: '/api/save/user-overrides',
  SAVE_AVAILABLE_DATA_STATUS: '/api/save/available-data',

  // ==================== ANONYMIZATION ====================
  ANONYMIZATION_NORMALIZE: '/api/additional_processing/normalize',
  ANONYMIZATION_GET_DEFAULT_RULES: '/api/additional_processing/get_default_rules',
  ANONYMIZATION_ANONYMIZE: '/api/additional_processing/anonymize',
  ANONYMIZATION_DOWNLOAD: '/api/additional_processing/download',

  // ==================== DATA STATUS ====================
  TEST_DATA: '/api/data/test-data',
  RESET_ANALYSIS: '/api/data/reset-analysis',
} as const;