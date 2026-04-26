// frontend/client/components/ui/CaseLifecycleTimeline.tsx

import { useState, useEffect } from "react";
import { apiClient } from "@/services/api/client";

interface StageItem {
  stageCode: string;
  stageName: string;
}

interface CaseLifecycleTimelineProps {
  stageCode: string;
  productionType?: 'lawsuit' | 'courtOrder';
  className?: string;
}

export function CaseLifecycleTimeline({ 
  stageCode, 
  productionType = 'lawsuit', 
  className = '' 
}: CaseLifecycleTimelineProps) {
  const [stages, setStages] = useState<StageItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Проверка на исключения — показывается отдельное сообщение вместо линии жизни
  if (stageCode && stageCode.includes('exceptions')) {
    return (
      <div className={`bg-bg-default-light-field border border-border-default rounded-lg p-4 text-center ${className}`}>
        <p className="text-text-secondary text-sm">Дело входит в ряд исключений из общих сроков</p>
      </div>
    );
  }

  // Загрузка этапов с бэкенда (исключения отфильтровываются)
  useEffect(() => {
    const type = productionType === 'courtOrder' ? 'order' : 'lawsuit';
    
    apiClient.get<{ success: boolean; stages: StageItem[] }>(
      `/api/case/stages/${type}`
    ).then(data => {
      if (data.success) {
        const filteredStages = data.stages.filter(
          stage => !stage.stageCode.includes('exceptions')
        );
        setStages(filteredStages);
      } else {
        setStages([]);
      }
    }).catch(() => setStages([]))
    .finally(() => setLoading(false));
  }, [productionType]);

  if (loading || stages.length === 0) {
    return null;
  }

  const currentIndex = stages.findIndex(stage => stage.stageCode === stageCode);
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
              width: `calc(${(currentIndex / (stages.length - 1)) * 100}%)`
            }}
          />

          {/* Точки */}
          <div className="absolute inset-0">
            {stages.map((stage, index) => {
              const isActive = index <= currentIndex;
              const leftPosition = `${(index / (stages.length - 1)) * 100}%`;
              
              return (
                <div
                  key={stage.stageCode}
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
          {stages.map((stage, index) => {
            const isActive = index <= currentIndex;
            const leftPosition = `${(index / (stages.length - 1)) * 100}%`;
            
            return (
              <div
                key={stage.stageCode}
                className="absolute -translate-x-1/2 text-center"
                style={{ left: leftPosition }}
              >
                <span
                  className={`text-xs whitespace-nowrap ${
                    isActive ? 'text-text-primary font-medium' : 'text-text-tertiary'
                  }`}
                >
                  {stage.stageName}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}