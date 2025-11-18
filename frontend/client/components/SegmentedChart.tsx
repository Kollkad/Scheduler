// SegmentedChart.tsx
import { useState, useRef, useEffect, useMemo } from 'react';
import { calculateBarHeights, generateTicks } from '@/utils/chartUtils';

interface Segment {
  name: string;
  label: string;
  value: number;
  color: string;
}

interface SegmentedChartProps {
  data: Array<{
    title: string;
    segments: Segment[];
    total: number;
  }>;
  maxValue?: number;
  onSegmentClick?: (stage: string, status: string, count: number) => void;
}

// Функция расчета максимального значения и шага
const calculateMaxValueAndTicks = (data: Array<{ total: number }>, customMaxValue?: number) => {
  if (customMaxValue) {
    return { maxValue: customMaxValue, tickStep: 1000 };
  }
  
  const maxVal = Math.max(...data.map(item => item.total), 1);
  
  let step;
  if (maxVal <= 12000) {
    step = 1000;
  } else {
    step = 3000;
  }
  
  const roundedMax = Math.ceil(maxVal / step) * step;
  
  return { maxValue: roundedMax, tickStep: step };
};

export function SegmentedChart({ data, maxValue, onSegmentClick }: SegmentedChartProps) {
  const [hoveredBar, setHoveredBar] = useState<string | null>(null);
  const [containerWidth, setContainerWidth] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Расчет максимального значения и делений с новой логикой
  const { maxValue: calculatedMaxValue, tickStep } = useMemo(() => {
    return calculateMaxValueAndTicks(data, maxValue);
  }, [data, maxValue]);
  
  // Расчет точных высот элементов графика
  const { barHeight, barGap, barsAreaHeight, xAxisHeight, totalChartHeight } = calculateBarHeights(data.length);
  const xTicks = generateTicks(calculatedMaxValue, tickStep);

  // Получение ширины контейнера для расчета минимальной ширины в пикселях
  useEffect(() => {
    const updateWidth = () => {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.offsetWidth);
      }
    };

    updateWidth();
    window.addEventListener('resize', updateWidth);
    
    return () => window.removeEventListener('resize', updateWidth);
  }, []);

  const handleBarHover = (name: string | null) => {
    setHoveredBar(name);
  };

  // Функция рассчитывает фактические ширины сегментов с учетом минимального размера
  const calculateSegmentWidths = (segments: Segment[], totalValue: number, barTotalWidth: number) => {
    const minWidthPixels = 15;
    
    return segments.map(segment => {
      if (segment.value === 0) return '0%';
      
      const percentageWidth = (segment.value / totalValue) * 100;
      const pixelWidth = (barTotalWidth * percentageWidth) / 100;
      
      // Использование минимальной ширины в пикселях при необходимости
      if (pixelWidth < minWidthPixels) {
        return `${minWidthPixels}px`;
      }
      
      return `${percentageWidth}%`;
    });
  };

  // Обработчик клика по сегменту столбца
  const handleSegmentClick = (stageName: string, segment: Segment) => {
    if (segment.value > 0 && onSegmentClick) {
      onSegmentClick(stageName, segment.name, segment.value);
    }
  };

  return (
    <div className="w-full max-w-[800px] mx-auto p-4 bg-white rounded-md shadow-sm pb-12">
      <div className="flex">
        {/* Подписи оси Y */}
        <div className="w-48 flex flex-col pr-2">
          {data.map((item, index) => {
            const isHovered = hoveredBar === item.title;
            return (
              <div 
                key={`label-${index}`} 
                className={`flex items-center justify-end text-right text-sm ${
                  isHovered ? 'font-bold text-green-500' : ''
                }`}
                style={{
                  height: `${barHeight}px`,
                  marginBottom: index < data.length - 1 ? `${barGap}px` : '0px'
                }}
              >
                {item.title}
              </div>
            );
          })}
        </div>

        {/* Область графика */}
        <div 
          ref={containerRef}
          className="flex-grow relative"
        >
          {/* Линия оси Y */}
          <div className="absolute left-0 top-0 bg-gray-800 z-10"
            style={{
              height: `${barsAreaHeight}px`,
              width: '1px'
            }}
          ></div>

          {/* Контейнер столбцов */}
          <div className="flex flex-col"
            style={{ height: `${barsAreaHeight}px` }}
          >
            {data.map((item, index) => {
              const isHovered = hoveredBar === item.title;
              
              // Ширина всей полосы в пикселях
              const barTotalWidth = containerWidth * (item.total / calculatedMaxValue);
              
              // Расчет ширины для всех сегментов
              const segmentWidths = calculateSegmentWidths(item.segments, item.total, barTotalWidth);
              
              return (
                <div 
                  key={`bar-${index}`}
                  className={`flex items-center transition-all duration-200 cursor-pointer ${
                    isHovered ? 'opacity-90 translate-x-0.5' : ''
                  }`}
                  style={{
                    height: `${barHeight}px`,
                    marginBottom: index < data.length - 1 ? `${barGap}px` : '0px'
                  }}
                  onMouseEnter={() => handleBarHover(item.title)}
                  onMouseLeave={() => handleBarHover(null)}
                  title={isHovered ? `Всего: ${item.total} дел` : ''}
                >
                  <div className="flex-grow h-full flex items-center bg-gray-100 rounded overflow-hidden relative">
                    {/* Сегментированный столбец */}
                    <div className={`h-full flex rounded border border-gray-300 overflow-visible ${
                      isHovered ? 'shadow-lg' : ''
                    }`}
                      style={{
                        width: `${(item.total / calculatedMaxValue) * 100}%`
                      }}
                    >
                      {item.segments.map((segment, segIndex) => {
                        if (segment.value === 0) return null;
                        
                        const isSegmentClickable = segment.value > 0 && onSegmentClick;
                        
                        return (
                          <div
                            key={segIndex}
                            className="h-full flex-shrink-0 min-w-[2px] border-r border-white last:border-r-0"
                            style={{
                              width: segmentWidths[segIndex],
                              backgroundColor: segment.color
                            }}
                            title={`${segment.label}: ${segment.value}`}
                            onClick={() => handleSegmentClick(item.title, segment)}
                          />
                        );
                      })}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Ось X с делениями */}
          <div className="absolute left-0 right-0 border-t border-gray-800"
            style={{
              top: `${barsAreaHeight}px`,
              height: `${xAxisHeight}px`
            }}
          >
            {xTicks.map(tick => (
              <div 
                key={`tick-${tick}`}
                className="absolute bottom-0 text-center"
                style={{
                  left: `${(tick / calculatedMaxValue) * 100}%`,
                  transform: 'translateX(-50%)'
                }}
              >
                <div className="h-1 w-px bg-gray-800 mx-auto"></div>
                <div className="text-sm text-gray-600 mt-0.5">
                  {tick}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}