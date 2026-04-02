// Header.tsx
import { Search, X, CircleUserRound } from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { useState, useRef, useEffect } from "react"; 
import { UploadFilesModal } from "./UploadFilesModal";
import { SavingModal } from "./SavingModal";
import { useCaseSearch } from "@/hooks/useCaseSearch";
import { useNavigate } from "react-router-dom";
import { useAnalysis } from "@/contexts/AnalysisContext"; 
import { ProgressBarModal } from "./ProgressBarModal";
import { useAdmin } from '@/hooks/useAdmin';

export function Header() {
  const { isAdmin, loading: adminLoading } = useAdmin();
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isSavingModalOpen, setIsSavingModalOpen] = useState(false);
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const [isProgressModalOpen, setIsProgressModalOpen] = useState(false);
  
  const { searchTerm, setSearchTerm, searchResults, hasResults } = useCaseSearch();
  const { isAnalyzing, runAnalysis } = useAnalysis(); 

  // Обработчик клика вне области поиска для скрытия результатов
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsSearchFocused(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Функция обрабатывает выбор результата поиска и переход к делу
  const handleResultClick = (caseCode: string) => {
    navigate(`/case/${caseCode}`);
    setSearchTerm('');
    setIsSearchFocused(false);
  };

  // Функция запускает процесс анализа данных
  const handleCalculate = async () => {
    console.log("Начинаем расчет...");
    setIsUploadModalOpen(false);
    setIsProgressModalOpen(true);
    
    try {
      await runAnalysis(); 
      console.log("Анализ завершен успешно");
    } catch (error) {
      console.error("Ошибка анализа:", error);
      setIsProgressModalOpen(false);
    }
  };
  // "Загрузить файлы"
  const handleUploadClick = () => {
    if (isAnalyzing) {
      setIsProgressModalOpen(true);
    } else {
      setIsUploadModalOpen(true);
    }
  };

  return (
    <header className="bg-white border-b border-border-default px-6 py-3 fixed top-0 left-80 right-0 z-10"
      style={{ 
      width: 'calc(100vw - 22rem)'
    }}>
      <div className="flex items-center justify-between">
        <div className="flex-1 max-w-md relative" ref={searchRef}>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-tertiary h-4 w-4" />
           <Input
              type="text"
              placeholder="Поиск по коду дела"
              className="pl-10 pr-10 h-9 bg-bg-default-light-field border-border-default focus:border-blue focus:ring-blue text-sm rounded-xl"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onFocus={() => setIsSearchFocused(true)}
            />
            {searchTerm && (
              <X 
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-text-tertiary h-4 w-4 cursor-pointer"
                onClick={() => setSearchTerm('')}
              />
            )}
          </div>

          {/* Отображение результатов поиска */}
          {isSearchFocused && hasResults && (
            <div className="absolute top-full left-0 right-0 bg-white border border-border-default rounded-lg shadow-lg mt-1 max-h-60 overflow-y-auto z-50">
              {searchResults.map((caseCode, index) => (
                <div
                  key={index}
                  className="px-4 py-2 hover:bg-bg-default-light-field cursor-pointer text-sm text-text-primary"
                  onClick={() => handleResultClick(caseCode)}
                >
                  {caseCode}
                </div>
              ))}
            </div>
          )}

          {/* Сообщение об отсутствии результатов */}
          {isSearchFocused && searchTerm && !hasResults && (
            <div className="absolute top-full left-0 right-0 bg-white border border-border-default rounded-lg shadow-lg mt-1 p-4 text-sm text-text-tertiary">
              Дело не найдено
            </div>
          )}
        </div>

        <div className="flex items-center space-x-3 ml-6">
          {!adminLoading && isAdmin && (
            <Button
              variant="green"
              size="rounded"
              onClick={handleUploadClick}
            >
              Загрузить файлы
            </Button>
          )}
                    
          <Button
            variant="grayOutline"
            size="rounded"
            onClick={() => setIsSavingModalOpen(true)}
          >
            Выгрузить данные
          </Button>
          <button
            onClick={() => navigate('/profile')}
            className="p-0 transition-colors hover:opacity-70"
          >
            <CircleUserRound className="w-9 h-9 text-text-tertiary" strokeWidth={1.5} />
          </button>
        </div>
      </div>

      <UploadFilesModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onCalculate={handleCalculate}
      />
      <SavingModal
        isOpen={isSavingModalOpen}
        onClose={() => setIsSavingModalOpen(false)}
      />
      <ProgressBarModal
        isOpen={isProgressModalOpen}
        onClose={() => setIsProgressModalOpen(false)}
      />
    </header>
  );
}