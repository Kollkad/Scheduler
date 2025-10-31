// ProgressBarModal.tsx
import { useState, useEffect, useRef } from "react";
import { X } from "lucide-react";
import { useAnalysis } from "@/contexts/AnalysisContext";

interface ProgressBarModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ProgressBarModal({ isOpen, onClose }: ProgressBarModalProps) {
  const { progress, isAnalyzing, analysisStatus } = useAnalysis();
  const modalRef = useRef<HTMLDivElement>(null);

  // Обработчик клика вне модального окна и нажатия Escape
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  // Автоматическое закрытие модального окна после завершения анализа
  useEffect(() => {
    if (isOpen && !isAnalyzing && analysisStatus.isComplete) {
      const timer = setTimeout(() => {
        onClose();
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [isOpen, isAnalyzing, analysisStatus.isComplete, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div
        ref={modalRef}
        className="bg-white rounded-2xl p-6 max-w-md w-full relative"
        style={{
          border: '1px solid #BDBDCC',
          boxShadow: '2px 4px 8px rgba(0, 0, 0, 0.1), -2px 0 8px rgba(0, 0, 0, 0.05)'
        }}
      >
        {/* Кнопка закрытия */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 hover:bg-gray-100 rounded-full transition-colors"
        >
          <X className="h-5 w-5" style={{ color: '#1F1F1F' }} />
        </button>

        {/* Заголовок */}
        <h2 className="text-xl font-semibold text-gray-900 mb-6 pr-8">
          Выполняется анализ данных
        </h2>

        {/* Прогресс-бар */}
        <div className="mb-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">
              Общий прогресс
            </span>
            <span className="text-sm text-gray-500">
              {progress?.progress || 0}%
            </span>
          </div>
          
          {/* Основной индикатор прогресса */}
          <div 
            className="w-full h-3 bg-gray-200 rounded-full overflow-hidden"
            style={{ border: '1px solid #BDBDCC' }}
          >
            <div 
              className="h-full rounded-full transition-all duration-300"
              style={{ 
                width: `${progress?.progress || 0}%`,
                backgroundColor: '#1CC53C'
              }}
            />
          </div>
        </div>

        {/* Отображение текущей задачи */}
        {progress && (
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-sm font-medium text-gray-700 mb-1">Текущая задача:</p>
            <p className="text-sm text-gray-600">{progress.currentTask}</p>
          </div>
        )}

        {/* Сообщение о завершении анализа */}
        {analysisStatus.isComplete && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm font-medium text-green-800 text-center">
              ✅ Анализ успешно завершен!
            </p>
          </div>
        )}

        {/* Информация о подключении */}
        <div className="mt-4 text-xs text-gray-500 text-center">
          Подключение к: http://localhost:8000
        </div>
      </div>
    </div>
  );
}