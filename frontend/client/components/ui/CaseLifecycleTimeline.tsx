import React from 'react';

const LAWSUIT_STAGES = [
  { key: 'firstStatusChanged', label: 'Подготовка документов' },
  { key: 'courtReaction', label: 'Ожидание реакции суда' },
  { key: 'underConsideration', label: 'На рассмотрении' },
  { key: 'decisionMade', label: 'Решение вынесено' },
  { key: 'executionDocumentReceived', label: 'ИД получен' },
  { key: 'closed', label: 'Закрыто' }
] as const;

const COURT_ORDER_STAGES = [
  { key: 'firstStatusChanged', label: 'Подготовка документов' },
  { key: 'courtReaction', label: 'Ожидание реакции суда' },
  { key: 'executionDocumentReceived', label: 'ИД получен' },
  { key: 'closed', label: 'Закрыто' }
] as const;

type ProductionType = 'lawsuit' | 'courtOrder';

interface CaseLifecycleTimelineProps {
  stageCode: string;
  productionType?: ProductionType;
  className?: string;
}

export function CaseLifecycleTimeline({ stageCode, productionType = 'lawsuit', className = '' }: CaseLifecycleTimelineProps) {
  if (stageCode === 'exceptions') {
    return (
      <div className={`bg-bg-default-light-field border border-border-default rounded-lg p-4 text-center ${className}`}>
        <p className="text-text-secondary text-sm">Дело входит в ряд исключений из общих сроков</p>
      </div>
    );
  }

  const STAGES = productionType === 'courtOrder' ? COURT_ORDER_STAGES : LAWSUIT_STAGES;
  const currentIndex = STAGES.findIndex(stage => stage.key === stageCode);
  if (currentIndex === -1) return null;

  return (
    <div className={`w-full ${className}`}>
      <div className="pt-8 pb-16 px-16">
        {/* Контейнер для линии и точек */}
        <div className="relative h-6">
          {/* Серая линия */}
          <div className="absolute top-1/2 left-0 w-full h-3 bg-bg-light-grey rounded-full -translate-y-1/2" />
          
          {/* Зеленая линия */}
          <div 
            className="absolute top-1/2 left-0 h-3 bg-green rounded-full -translate-y-1/2 transition-all duration-300"
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
                      isActive ? 'bg-green' : 'bg-bg-light-grey'
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
                    isActive ? 'text-text-primary font-medium' : 'text-text-tertiary'
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