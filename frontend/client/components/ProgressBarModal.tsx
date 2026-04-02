// client\components\ProgressBarModal.tsx
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
    <div className="fixed inset-0 bg-bg-medium-gray flex items-center justify-center z-50 p-4">
      <div
        ref={modalRef}
        className="bg-white rounded-2xl p-6 max-w-md w-full relative border border-border-default"
        style={{
          boxShadow: '2px 4px 8px rgba(0, 0, 0, 0.1), -2px 0 8px rgba(0, 0, 0, 0.05)'
        }}
      >
        {/* Кнопка закрытия */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 hover:bg-bg-light-grey rounded-full transition-colors"
        >
          <X className="h-5 w-5 text-dark-default" />
        </button>

        {/* Заголовок */}
        <h2 className="text-xl font-semibold text-text-primary mb-6 pr-8">
          Выполняется анализ данных
        </h2>

        {/* Прогресс-бар */}
        <div className="mb-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-text-secondary">
              Общий прогресс
            </span>
            <span className="text-sm text-text-tertiary">
              {progress?.progress || 0}%
            </span>
          </div>
          
          {/* Основной индикатор прогресса */}
          <div 
            className="w-full h-3 bg-bg-default-light-field rounded-full overflow-hidden border border-border-default"
          >
            <div 
              className="h-full rounded-full transition-all duration-300 bg-green"
              style={{ width: `${progress?.progress || 0}%` }}
            />
          </div>
        </div>

        {/* Отображение текущей задачи */}
        {progress && (
          <div className="p-3 bg-bg-default-light-field rounded-lg">
            <p className="text-sm font-medium text-text-primary mb-1">Текущая задача:</p>
            <p className="text-sm text-text-secondary">{progress.currentTask}</p>
          </div>
        )}

        {/* Сообщение о завершении анализа */}
        {analysisStatus.isComplete && (
          <div className="mt-4 p-3 bg-bg-light-green border border-green rounded-lg">
            <p className="text-sm font-medium text-green-dark text-center">
              ✅ Анализ успешно завершен!
            </p>
          </div>
        )}
      </div>
    </div>
  );
}