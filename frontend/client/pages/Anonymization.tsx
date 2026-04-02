// client/pages/Anonymization.tsx
import { useState, useRef } from "react";
import { PageContainer } from "@/components/PageContainer";
import { Button } from "@/components/ui/button";
import { X, Loader2 } from "lucide-react";
import { apiClient } from "@/services/api/client";
import { API_ENDPOINTS } from "@/services/api/endpoints";

type NormalizationType = "detailed_report" | "documents_report" | "none";

interface CustomRuleInput {
  column: string;
  type: 'numbered' | 'fixed';
  replacement: string;
}

// ==================== ТИПЫ ДЛЯ ОБЕЗЛИЧИВАНИЯ ====================

export interface AnonymizationRule {
  column: string;
  type: 'numbered' | 'fixed';
  replacement: string;
}

export interface ColumnInfo {
  name: string;
  type: string;
  unique_count: number;
  total_count: number;
  sample: string[];
}

export interface NormalizeResponse {
  success: boolean;
  message: string;
  filename: string;
  rows: number;
  columns: number;
  columns_info: ColumnInfo[];
  applicable_rules: AnonymizationRule[];
  applicable_rules_count: number;
  total_rules_in_config: number;
}

export interface AnonymizeResponse {
  success: boolean;
  message: string;
  result_file_type: string;
  rows: number;
  columns: number;
  total_rules_applied: number;
  anonymization_results: Array<{
    column: string;
    type: string;
    original_unique: number;
    anonymized_unique: number;
    replacement: string;
  }>;
}

export interface DefaultRulesResponse {
  success: boolean;
  rules: AnonymizationRule[];
  total_rules: number;
  note: string;
}

export default function Anonymization() {
  // Состояние выбранного файла
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  // Тип нормализации: детальный отчет, отчет документов или без нормализации
  const [normalizationType, setNormalizationType] = useState<NormalizationType>("none");
  // Состояния процесса загрузки и нормализации
  const [uploadLoading, setUploadLoading] = useState(false);
  const [normalizeLoading, setNormalizeLoading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [fileUploaded, setFileUploaded] = useState(false);
  const [sourceFileType, setSourceFileType] = useState<string | null>(null);
  
  // Данные о колонках и правилах, полученные после нормализации
  const [columnsInfo, setColumnsInfo] = useState<ColumnInfo[]>([]);
  const [defaultRules, setDefaultRules] = useState<AnonymizationRule[]>([]);
  const [enabledRules, setEnabledRules] = useState<AnonymizationRule[]>([]);
  
  // Пользовательские правила (добавляются вручную)
  const [customRules, setCustomRules] = useState<CustomRuleInput[]>([
    { column: "", type: 'numbered', replacement: "" }
  ]);
  
  const [anonymizeLoading, setAnonymizeLoading] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };
  
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setUploadSuccess(false);
      setUploadError(null);
      setColumnsInfo([]);
      setDefaultRules([]);
      setEnabledRules([]);
      setSourceFileType(null);
    }
  };
  
  // 1. Загрузка файла через общее хранилище с типом anonymization_source
  const handleUploadFile = async () => {
    if (!selectedFile) return;
    
    setUploadLoading(true);
    setUploadError(null);
    
    try {
      const response = await apiClient.uploadFileByType('anonymization_source', selectedFile);
      setSourceFileType('anonymization_source');
      setFileUploaded(true);
      
      // После успешной загрузки выполняется нормализация
      setNormalizeLoading(true);
      await handleNormalize('anonymization_source');
      
    } catch (error) {
      console.error('Ошибка загрузки файла:', error);
      setUploadError(error instanceof Error ? error.message : 'Неизвестная ошибка');
    } finally {
      setUploadLoading(false);
      setNormalizeLoading(false);
    }
  };
  
  // 2. Нормализация загруженного файла в зависимости от выбранного типа
  const handleNormalize = async (fileType: string) => {
    try {
      const response = await apiClient.post<NormalizeResponse>(
        API_ENDPOINTS.ANONYMIZATION_NORMALIZE,
        null,
        {
          params: {
            file_type: fileType,
            normalization_type: normalizationType
          }
        }
      );
      
      if (response.success) {
        setColumnsInfo(response.columns_info || []);
        setDefaultRules(response.applicable_rules || []);
        setEnabledRules(response.applicable_rules || []);
        setUploadSuccess(true);
      } else {
        throw new Error(response.message || "Ошибка нормализации");
      }
      
    } catch (error) {
      console.error('Ошибка нормализации:', error);
      setUploadError(error instanceof Error ? error.message : 'Ошибка нормализации');
      throw error;
    }
  };
  
  // Удаление файла из хранилища и сброс локального состояния
  const handleRemoveFile = async () => {
    if (sourceFileType) {
      try {
        await apiClient.removeFile(sourceFileType);
      } catch (error) {
        console.error('Ошибка удаления файла:', error);
      }
    }
    
    setSelectedFile(null);
    setFileUploaded(false);
    setUploadSuccess(false);
    setColumnsInfo([]);
    setDefaultRules([]);
    setEnabledRules([]);
    setUploadError(null);
    setSourceFileType(null);
  };
  
  const handleToggleRule = (rule: AnonymizationRule, checked: boolean) => {
    if (checked) {
      setEnabledRules(prev => [...prev, rule]);
    } else {
      setEnabledRules(prev => prev.filter(r => 
        !(r.column === rule.column && r.type === rule.type && r.replacement === rule.replacement)
      ));
    }
  };
  
  const handleAddCustomRule = () => {
    setCustomRules(prev => [...prev, { column: "", type: 'numbered', replacement: "" }]);
  };
  
  const handleCustomRuleChange = (index: number, field: keyof CustomRuleInput, value: string) => {
    setCustomRules(prev => {
      const newRules = [...prev];
      if (field === 'type') {
        newRules[index][field] = value as 'numbered' | 'fixed';
      } else {
        newRules[index][field] = value;
      }
      return newRules;
    });
  };
  
  const handleRemoveCustomRule = (index: number) => {
    setCustomRules(prev => prev.filter((_, i) => i !== index));
  };
  
  // 3. Применение обезличивания к нормализованным данным
  const handleAnonymize = async () => {
    if (!sourceFileType) {
      alert("Сначала загрузите файл");
      return;
    }
    
    try {
      setAnonymizeLoading(true);
      
      // Формирование активных правил: выбранные из стандартных + пользовательские
      const activeRules = [...enabledRules];
      
      customRules.forEach(rule => {
        if (rule.column.trim() && rule.replacement.trim()) {
          activeRules.push({
            column: rule.column.trim(),
            type: rule.type,
            replacement: rule.replacement.trim()
          });
        }
      });
      
      if (activeRules.length === 0) {
        alert("Нет правил для обезличивания!");
        setAnonymizeLoading(false);
        return;
      }
      
      const response = await apiClient.post<AnonymizeResponse>(
        API_ENDPOINTS.ANONYMIZATION_ANONYMIZE,
        {
          config_json: JSON.stringify(activeRules),
          use_default_rules: true
        },
        {
          params: {
            file_type: sourceFileType
          }
        }
      );
      
      if (response.success) {
        // Скачивание обезличенного файла
        const blob = await apiClient.downloadFile(API_ENDPOINTS.ANONYMIZATION_DOWNLOAD, {
          file_type: 'anonymization_result'
        });
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${selectedFile?.name.replace('.xlsx', '')}_anonymized.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        
        alert(`Обезличивание завершено! Применено правил: ${response.total_rules_applied}`);
      }
      
    } catch (error) {
      console.error('Ошибка обезличивания:', error);
      alert(error instanceof Error ? error.message : 'Ошибка обезличивания');
    } finally {
      setAnonymizeLoading(false);
    }
  };
  
  // Загрузка правил по умолчанию из конфигурации (вызывается при монтировании)
  const loadDefaultRules = async () => {
    try {
      const response = await apiClient.get<DefaultRulesResponse>(API_ENDPOINTS.ANONYMIZATION_GET_DEFAULT_RULES);
      if (response.success) {
        setDefaultRules(response.rules);
      }
    } catch (error) {
      console.error('Ошибка загрузки правил:', error);
    }
  };
  
  return (
    <PageContainer>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-text-primary mb-2">Обезличивание отчетов</h1>
        <p className="text-text-secondary">
          Загрузите файл для удаления персональных данных
        </p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Левая колонка: загрузка файла и выбор типа нормализации */}
        <div>
          {/* Выбор типа нормализации влияет на предобработку файла */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Тип отчета
            </label>
            <div className="flex gap-4">
              <label className="flex items-center text-text-primary">
                <input
                  type="radio"
                  name="normalizationType"
                  value="detailed_report"
                  checked={normalizationType === "detailed_report"}
                  onChange={(e) => setNormalizationType(e.target.value as NormalizationType)}
                  className="mr-2 text-green focus:ring-blue"
                />
                Детальный отчет
              </label>
              <label className="flex items-center text-text-primary">
                <input
                  type="radio"
                  name="normalizationType"
                  value="documents_report"
                  checked={normalizationType === "documents_report"}
                  onChange={(e) => setNormalizationType(e.target.value as NormalizationType)}
                  className="mr-2 text-green focus:ring-blue"
                />
                Отчет по документам
              </label>
              <label className="flex items-center text-text-primary">
                <input
                  type="radio"
                  name="normalizationType"
                  value="none"
                  checked={normalizationType === "none"}
                  onChange={(e) => setNormalizationType(e.target.value as NormalizationType)}
                  className="mr-2 text-green focus:ring-blue"
                />
                Иной отчет
              </label>
            </div>
          </div>
          
          {/* Выбор файла с интерфейсом, аналогичным модальному окну загрузки */}
          <div className="mb-6">
            <div className="flex items-center gap-3 mb-4">
              <div 
                className={`flex-1 border-b border-border-default py-2 min-h-[40px] flex items-center overflow-hidden max-w-lg
                  ${!fileUploaded ? 
                    'cursor-pointer hover:border-green transition-colors duration-200' : 
                    'cursor-default'}`}
                onClick={!fileUploaded ? triggerFileInput : undefined}
              >
                {selectedFile ? (
                  <div className="flex items-center gap-2 min-w-0 flex-1">
                    <span className="text-text-primary truncate">{selectedFile.name}</span>
                  </div>
                ) : (
                  <span className="text-text-tertiary">Выберите файл отчета (.xlsx, .xls)</span>
                )}
              </div>
              
              {!fileUploaded ? (
                <Button
                  onClick={triggerFileInput}
                  variant="green"
                  size="rounded"
                >
                  Выбрать файл
                </Button>
              ) : (
                <div className="flex gap-2">
                  <Button
                    onClick={triggerFileInput}
                    variant="grayOutline"
                    size="rounded"
                  >
                    Заменить
                  </Button>
                  <Button
                    onClick={handleRemoveFile}
                    variant="grayOutline"
                    size="rounded"
                  >
                    Удалить
                  </Button>
                </div>
              )}
              
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls"
                className="hidden"
                onChange={handleFileSelect}
              />
            </div>
            
            {/* Кнопка запуска процесса загрузки и нормализации */}
            {selectedFile && !uploadSuccess && (
              <div className="max-w-lg">
                <Button
                  onClick={handleUploadFile}
                  variant="green"
                  size="rounded"
                  disabled={uploadLoading || normalizeLoading}
                  className="w-full"
                >
                  {(uploadLoading || normalizeLoading) ? (
                    <div className="flex items-center justify-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Подождите, идет загрузка...</span>
                    </div>
                  ) : (
                    "Загрузить для обезличивания"
                  )}
                </Button>
              </div>
            )}
            
            {uploadError && (
              <p className="text-red text-sm mt-2">Ошибка: {uploadError}</p>
            )}
            
            {uploadSuccess && (
              <div className="text-green text-sm mt-2">
                ✓ Отчет загружен и нормализован. Колонок: {columnsInfo.length}, правил: {defaultRules.length}
              </div>
            )}
          </div>
        </div>
        
        {/* Правая колонка: управление правилами обезличивания (отображается после успешной нормализации) */}
        {uploadSuccess && (
          <div>
            {/* Стандартные правила, применимые к колонкам отчета */}
            {defaultRules.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-medium text-text-primary mb-3">
                  Правила обезличивания ({defaultRules.length})
                </h3>
                <div className="space-y-2 max-h-60 overflow-y-auto border border-border-default rounded-lg p-4 bg-white">
                  {defaultRules.map((rule, index) => {
                    const isEnabled = enabledRules.some(r => 
                      r.column === rule.column && r.type === rule.type && r.replacement === rule.replacement
                    );
                    
                    return (
                      <div key={index} className="flex items-center gap-3 p-2 hover:bg-bg-default-light-field rounded">
                        <input
                          type="checkbox"
                          id={`rule-${index}`}
                          checked={isEnabled}
                          onChange={(e) => handleToggleRule(rule, e.target.checked)}
                          className="h-4 w-4 text-green focus:ring-blue border-border-default rounded"
                        />
                        <label htmlFor={`rule-${index}`} className="flex-1 cursor-pointer">
                          <div className="font-medium text-sm text-text-primary">{rule.column}</div>
                          <div className="text-xs text-text-tertiary">
                            {rule.type === 'numbered' ? 'Нумерованная замена' : 'Фиксированная замена'} → "{rule.replacement}"
                          </div>
                        </label>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
            
            {/* Пользовательские правила: добавляются вручную для любых колонок */}
            <div className="mb-6">
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-lg font-medium text-text-primary">
                  Дополнительные правила
                </h3>
                <Button
                  onClick={handleAddCustomRule}
                  variant="grayOutline"
                  size="rounded"
                >
                  + Добавить правило
                </Button>
              </div>
              
              <div className="space-y-4 border border-border-default rounded-lg p-4 bg-white">
                {customRules.map((rule, index) => (
                  <div key={index} className="relative">
                    {customRules.length > 1 && (
                      <button
                        onClick={() => handleRemoveCustomRule(index)}
                        className="absolute -right-2 -top-2 bg-red text-white rounded-full p-1 hover:bg-red-transparent z-10"
                        aria-label="Удалить правило"
                      >
                        <X size={16} />
                      </button>
                    )}
                    
                    <div className="p-3 border border-border-default rounded-2xl">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        <div>
                          <label className="block text-xs text-text-tertiary mb-1">Колонка</label>
                          <input
                            type="text"
                            value={rule.column}
                            onChange={(e) => handleCustomRuleChange(index, 'column', e.target.value)}
                            placeholder="Название колонки"
                            className="w-full px-3 py-2 border border-border-default rounded-lg text-sm text-text-primary bg-white focus:outline-none focus:ring-2 focus:ring-blue focus:border-transparent"
                          />
                        </div>
                        
                        <div>
                          <label className="block text-xs text-text-tertiary mb-1">Текст замены</label>
                          <input
                            type="text"
                            value={rule.replacement}
                            onChange={(e) => handleCustomRuleChange(index, 'replacement', e.target.value)}
                            placeholder="Текст для замены"
                            className="w-full px-3 py-2 border border-border-default rounded-lg text-sm text-text-primary bg-white focus:outline-none focus:ring-2 focus:ring-blue focus:border-transparent"
                          />
                        </div>
                        
                        <div>
                          <label className="block text-xs text-text-tertiary mb-1">Тип замены</label>
                          <select
                            value={rule.type}
                            onChange={(e) => handleCustomRuleChange(index, 'type', e.target.value as 'numbered' | 'fixed')}
                            className="w-full px-3 py-2 border border-border-default rounded-lg text-sm text-text-primary bg-white focus:outline-none focus:ring-2 focus:ring-blue focus:border-transparent"
                          >
                            <option value="numbered">Нумерованная</option>
                            <option value="fixed">Фиксированная</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Кнопка запуска обезличивания (доступна после успешной нормализации) */}
      {uploadSuccess && (
        <div className="mt-8 border-t border-border-default pt-6">
          <div className="max-w-lg mx-auto">
            <Button
              onClick={handleAnonymize}
              variant="green"
              size="rounded"
              disabled={anonymizeLoading}
              className="w-full py-3 text-lg"
            >
              {anonymizeLoading ? (
                <div className="flex items-center justify-center gap-2">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>Обезличивание...</span>
                </div>
              ) : (
                "Обезличить и скачать"
              )}
            </Button>
          </div>
        </div>
      )}
    </PageContainer>
  );
}


