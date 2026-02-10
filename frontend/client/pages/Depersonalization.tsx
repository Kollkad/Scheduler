import { useState, useRef } from "react";
import { PageContainer } from "@/components/PageContainer";
import { Button } from "@/components/ui/button";
import { X, Loader2 } from "lucide-react";

type ReportType = "detailed_report" | "documents_report";

interface AnonymizationRule {
  column: string;
  type: 'numbered' | 'fixed';
  replacement: string;
}

interface ColumnInfo {
  name: string;
  type: string;
  unique_count: number;
  total_count: number;
  sample: string[];
}

interface CustomRuleInput {
  column: string;
  type: 'numbered' | 'fixed';
  replacement: string;
}

export default function Depersonalization() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [reportType, setReportType] = useState<ReportType>("detailed_report");
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [fileUploaded, setFileUploaded] = useState(false);
  
  const [columnsInfo, setColumnsInfo] = useState<ColumnInfo[]>([]);
  const [defaultRules, setDefaultRules] = useState<AnonymizationRule[]>([]);
  const [enabledRules, setEnabledRules] = useState<AnonymizationRule[]>([]);
  
  const [customRules, setCustomRules] = useState<CustomRuleInput[]>([
    { column: "", type: 'numbered', replacement: "" }
  ]);
  
  // Состояние для загрузки обезличивания
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
    }
  };
  
  const handleUploadReport = async () => {
    if (!selectedFile) return;
    
    setUploadLoading(true);
    setUploadError(null);
    
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('report_type', reportType);
      
      const response = await fetch(
        `http://localhost:8000/api/additional_processing/load_report`,
        {
          method: 'POST',
          body: formData,
        }
      );
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Ошибка загрузки: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        setColumnsInfo(data.columns_info || []);
        setDefaultRules(data.applicable_rules || []);
        setEnabledRules(data.applicable_rules || []);
        setUploadSuccess(true);
        setFileUploaded(true);
      } else {
        throw new Error(data.message || "Ошибка загрузки");
      }
      
    } catch (error) {
      console.error('Ошибка загрузки отчета:', error);
      setUploadError(error instanceof Error ? error.message : 'Неизвестная ошибка');
    } finally {
      setUploadLoading(false);
    }
  };
  
  const handleRemoveFile = () => {
    setSelectedFile(null);
    setFileUploaded(false);
    setUploadSuccess(false);
    setColumnsInfo([]);
    setDefaultRules([]);
    setEnabledRules([]);
    setUploadError(null);
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
  
  const handleAnonymize = async () => {
    try {
      setAnonymizeLoading(true);
      
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
      
      const formData = new FormData();
      formData.append('report_type', reportType);
      formData.append('config_json', JSON.stringify(activeRules));
      formData.append('use_default_rules', 'true');
      
      const response = await fetch(
        `http://localhost:8000/api/additional_processing/anonymize`,
        {
          method: 'POST',
          body: formData,
        }
      );
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Ошибка обезличивания: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        const downloadResponse = await fetch(
          `http://localhost:8000/api/additional_processing/download_anonymized?report_type=${reportType}`
        );
        
        if (downloadResponse.ok) {
          const blob = await downloadResponse.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `${selectedFile?.name.replace('.xlsx', '')}_anonymized.xlsx`;
          document.body.appendChild(a);
          a.click();
          a.remove();
          window.URL.revokeObjectURL(url);
          
          alert(`Обезличивание завершено! Применено правил: ${result.total_rules_applied}`);
        } else {
          throw new Error("Ошибка скачивания файла");
        }
      }
      
    } catch (error) {
      console.error('Ошибка обезличивания:', error);
      alert(error instanceof Error ? error.message : 'Ошибка обезличивания');
    } finally {
      setAnonymizeLoading(false);
    }
  };
  
  return (
    <PageContainer>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Обезличивание отчетов</h1>
        <p className="text-gray-600">
          Загрузите отчет для удаления персональных данных
        </p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* ЛЕВАЯ КОЛОНКА - ЗАГРУЗКА ФАЙЛА */}
        <div>
          {/* Выбор типа отчета */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Тип отчета
            </label>
            <div className="flex gap-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="reportType"
                  value="detailed_report"
                  checked={reportType === "detailed_report"}
                  onChange={(e) => setReportType(e.target.value as ReportType)}
                  className="mr-2"
                />
                Детальный отчет
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="reportType"
                  value="documents_report"
                  checked={reportType === "documents_report"}
                  onChange={(e) => setReportType(e.target.value as ReportType)}
                  className="mr-2"
                />
                Отчет по документам
              </label>
            </div>
          </div>
          
          {/* Выбор файла с умными кнопками как в модалке */}
          <div className="mb-6">
            <div className="flex items-center gap-3 mb-4">
              <div 
                className={`flex-1 border-b border-gray-300 py-2 min-h-[40px] flex items-center overflow-hidden max-w-lg
                  ${!fileUploaded ? 
                    'cursor-pointer hover:border-green-500 transition-colors duration-200' : 
                    'cursor-default'}`}
                onClick={!fileUploaded ? triggerFileInput : undefined}
              >
                {selectedFile ? (
                  <div className="flex items-center gap-2 min-w-0 flex-1">
                    <span className="text-gray-900 truncate">{selectedFile.name}</span>
                  </div>
                ) : (
                  <span className="text-gray-400">Выберите файл отчета (.xlsx, .xls)</span>
                )}
              </div>
              
              {/* Умные кнопки как в модалке */}
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
            
            {/* Кнопка загрузки на сервер (показывается при выбранном файле, но еще не загруженном) */}
            {selectedFile && !fileUploaded && (
              <div className="max-w-lg">
                <Button
                  onClick={handleUploadReport}
                  variant="green"
                  size="rounded"
                  disabled={uploadLoading}
                  className="w-full transition-all duration-200"
                  style={{
                    opacity: uploadLoading ? 0.8 : 1,
                    backgroundColor: uploadLoading ? 'rgba(34, 197, 94, 0.8)' : undefined
                  }}
                >
                  {uploadLoading ? (
                    <div className="flex items-center justify-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Загрузка...</span>
                    </div>
                  ) : (
                    "Загрузить для обезличивания"
                  )}
                </Button>
              </div>
            )}
            
            {uploadError && (
              <p className="text-red-500 text-sm mt-2">Ошибка: {uploadError}</p>
            )}
            
            {uploadSuccess && (
              <div className="text-green-600 text-sm mt-2">
                ✓ Отчет загружен успешно. Колонок: {columnsInfo.length}, правил: {defaultRules.length}
              </div>
            )}
          </div>
        </div>
        
        {/* ПРАВАЯ КОЛОНКА - ПРАВИЛА (появляется после загрузки) */}
        {uploadSuccess && (
          <div>
            {/* Правила по умолчанию */}
            {defaultRules.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-medium text-gray-900 mb-3">
                  Правила обезличивания ({defaultRules.length})
                </h3>
                <div className="space-y-2 max-h-60 overflow-y-auto border border-gray-200 rounded-lg p-4 bg-white">
                  {defaultRules.map((rule, index) => {
                    const isEnabled = enabledRules.some(r => 
                      r.column === rule.column && r.type === rule.type && r.replacement === rule.replacement
                    );
                    
                    return (
                      <div key={index} className="flex items-center gap-3 p-2 hover:bg-gray-50 rounded">
                        <input
                          type="checkbox"
                          id={`rule-${index}`}
                          checked={isEnabled}
                          onChange={(e) => handleToggleRule(rule, e.target.checked)}
                          className="h-4 w-4"
                        />
                        <label htmlFor={`rule-${index}`} className="flex-1 cursor-pointer">
                          <div className="font-medium text-sm">{rule.column}</div>
                          <div className="text-xs text-gray-500">
                            {rule.type === 'numbered' ? 'Нумерованная замена' : 'Фиксированная замена'} → "{rule.replacement}"
                          </div>
                        </label>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
            
            {/* Кастомные правила */}
            <div className="mb-6">
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-lg font-medium text-gray-900">
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
              
              <div className="space-y-4 border border-gray-200 rounded-lg p-4 bg-white">
                {customRules.map((rule, index) => (
                  <div key={index} className="relative">
                    {customRules.length > 1 && (
                      <button
                        onClick={() => handleRemoveCustomRule(index)}
                        className="absolute -right-2 -top-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600 z-10"
                        aria-label="Удалить правило"
                      >
                        <X size={16} />
                      </button>
                    )}
                    
                    <div className="p-3 border border-gray-200 rounded-2xl">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        <div>
                          <label className="block text-xs text-gray-500 mb-1">Колонка</label>
                          <input
                            type="text"
                            value={rule.column}
                            onChange={(e) => handleCustomRuleChange(index, 'column', e.target.value)}
                            placeholder="Название колонки"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                          />
                        </div>
                        
                        <div>
                          <label className="block text-xs text-gray-500 mb-1">Текст замены</label>
                          <input
                            type="text"
                            value={rule.replacement}
                            onChange={(e) => handleCustomRuleChange(index, 'replacement', e.target.value)}
                            placeholder="Текст для замены"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                          />
                        </div>
                        
                        <div>
                          <label className="block text-xs text-gray-500 mb-1">Тип замены</label>
                          <select
                            value={rule.type}
                            onChange={(e) => handleCustomRuleChange(index, 'type', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
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
      
      {/* Кнопка обезличивания */}
      {uploadSuccess && (
        <div className="mt-8 border-t pt-6">
          <div className="max-w-lg mx-auto">
            <Button
              onClick={handleAnonymize}
              variant="green"
              size="rounded"
              disabled={anonymizeLoading}
              className="w-full py-3 text-lg transition-all duration-200"
              style={{
                opacity: anonymizeLoading ? 0.8 : 1,
                backgroundColor: anonymizeLoading ? 'rgba(34, 197, 94, 0.8)' : undefined
              }}
            >
              {anonymizeLoading ? (
                <div className="flex items-center justify-center gap-2">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>Подождите минутку...</span>
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