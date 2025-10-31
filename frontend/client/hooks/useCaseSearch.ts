// src/hooks/useCaseSearch.ts
import { useState, useMemo } from 'react';
import { useAnalysis } from '@/contexts/AnalysisContext';

export function useCaseSearch() {
  const [searchTerm, setSearchTerm] = useState('');
  const { 
    rainbowResult, 
    documentsResult, 
    termsV2LawsuitResult,
    termsV2OrderResult 
  } = useAnalysis();

  // Хук собирает все коды дел из различных источников анализа данных
  const allCaseCodes = useMemo(() => {
    const codes = new Set<string>();
    
    // Функция извлекает коды дел из данных различных форматов
    const extractCaseCodes = (data: any): string[] => {
      if (!data) return [];
      
      // Обработка данных в формате массива
      if (Array.isArray(data)) {
        return data
          .map((item: any) => item.case_code || item.caseCode || '')
          .filter(Boolean);
      }
      
      // Обработка данных с полем cases
      if (data.cases && Array.isArray(data.cases)) {
        return data.cases
          .map((item: any) => item.case_code || item.caseCode || '')
          .filter(Boolean);
      }
      
      // Обработка данных с полем data
      if (data.data && Array.isArray(data.data)) {
        return data.data
          .map((item: any) => item.case_code || item.caseCode || '')
          .filter(Boolean);
      }
      
      // Логирование для отладки неизвестных форматов данных
      console.log('Unknown data format:', data);
      return [];
    };

    // Извлечение кодов из анализа Rainbow
    if (rainbowResult?.success) {
      const rainbowCodes = extractCaseCodes(rainbowResult.data);
      rainbowCodes.forEach(code => codes.add(code));
    }
    
    // Извлечение кодов из анализа документов
    if (documentsResult?.success) {
      const documentsCodes = extractCaseCodes(documentsResult.data);
      documentsCodes.forEach(code => codes.add(code));
    }
    
    // Извлечение кодов из анализа искового производства
    if (termsV2LawsuitResult?.success) {
      const lawsuitCodes = extractCaseCodes(termsV2LawsuitResult.data);
      lawsuitCodes.forEach(code => codes.add(code));
    }
    
    // Извлечение кодов из анализа приказного производства
    if (termsV2OrderResult?.success) {
      const orderCodes = extractCaseCodes(termsV2OrderResult.data);
      orderCodes.forEach(code => codes.add(code));
    }
    
    console.log('Available case codes:', Array.from(codes));
    return Array.from(codes).sort();
  }, [rainbowResult, documentsResult, termsV2LawsuitResult, termsV2OrderResult]);

  // Поиск кодов дел с частичным совпадением по введенному термину
  const searchResults = useMemo(() => {
    if (!searchTerm.trim()) return [];
    
    return allCaseCodes.filter(code =>
      code.toLowerCase().includes(searchTerm.toLowerCase())
    ).slice(0, 20); // Ограничение количества результатов для производительности
  }, [searchTerm, allCaseCodes]);

  return {
    searchTerm,
    setSearchTerm,
    searchResults,
    hasResults: searchResults.length > 0
  };
}