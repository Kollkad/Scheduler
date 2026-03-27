import React from 'react';

const STAGES = [
  { key: 'firstStatusChanged', label: 'Подготовка документов' },
    { key: 'courtReaction', label: 'Ожидание реакции суда' },
  { key: 'underConsideration', label: 'На рассмотрении' },
  { key: 'decisionMade', label: 'Решение вынесено' },
  { key: 'executionDocumentReceived', label: 'ИД получен' },
  { key: 'closed', label: 'Закрыто' }
] as const;

interface CaseLifecycleTimelineProps {
  caseStage: string;
  className?: string;
}

export function CaseLifecycleTimeline({ caseStage, className = '' }: CaseLifecycleTimelineProps) {
  if (caseStage === 'exceptions') {
    return (
      <div className={`bg-gray-50 border border-gray-200 rounded-lg p-4 text-center ${className}`}>
        <p className="text-gray-600 text-sm">Дело входит в ряд исключений из общих сроков</p>
      </div>
    );
  }

  const currentIndex = STAGES.findIndex(stage => stage.key === caseStage);
  if (currentIndex === -1) return null;

  return (
    <div className={`w-full ${className}`}>
      <div className="pt-8 pb-16 px-16">
        {/* Контейнер для линии и точек */}
        <div className="relative h-6">
          {/* Серая линия */}
          <div className="absolute top-1/2 left-0 w-full h-3 bg-gray-200 rounded-full -translate-y-1/2" />
          
          {/* Зеленая линия */}
          <div 
            className="absolute top-1/2 left-0 h-3 bg-green-500 rounded-full -translate-y-1/2 transition-all duration-300"
            style={{ 
              width: `calc(${(currentIndex / (STAGES.length - 1)) * 100}%)`
            }}
          />

          {/* Точки*/}
          <div className="absolute inset-0">
            {STAGES.map((stage, index) => {
              const isActive = index <= currentIndex;
              const leftPosition = `${(index / (STAGES.length - 1)) * 100}%`;
              
              return (
                <div
                  key={stage.key}
                  className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2"
                  style={{ left: leftPosition }}
                >
                  <div
                    className={`w-5 h-5 rounded-full ${
                      isActive ? 'bg-green-500' : 'bg-gray-300'
                    }`}
                  />
                </div>
              );
            })}
          </div>
        </div>

        {/* Подписи */}
        <div className="relative h-8 mt-4">
          {STAGES.map((stage, index) => {
            const isActive = index <= currentIndex;
            const leftPosition = `${(index / (STAGES.length - 1)) * 100}%`;
            
            return (
              <div
                key={stage.key}
                className="absolute -translate-x-1/2 text-center"
                style={{ left: leftPosition }}
              >
                <span
                  className={`text-xs whitespace-nowrap ${
                    isActive ? 'text-gray-900 font-medium' : 'text-gray-400'
                  }`}
                >
                  {stage.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}