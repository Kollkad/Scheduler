// SegmentedChart.tsx
import { useState, useRef, useEffect } from 'react';
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

export function SegmentedChart({ data, maxValue = 140, onSegmentClick }: SegmentedChartProps) {
  const [hoveredBar, setHoveredBar] = useState<string | null>(null);
  const [containerWidth, setContainerWidth] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Расчет точных высот элементов графика
  const { barHeight, barGap, barsAreaHeight, xAxisHeight, totalChartHeight } = calculateBarHeights(data.length);
  const xTicks = generateTicks(maxValue);

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
    const minWidthPixels = 10;
    
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
    <div style={{
      fontFamily: 'Arial, sans-serif',
      maxWidth: '800px',
      margin: '0 auto',
      padding: '20px',
      background: 'white',
      borderRadius: '8px',
      boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)'
    }}>
      <div style={{ display: 'flex', height: `${totalChartHeight}px` }}>
        {/* Подписи оси Y */}
        <div style={{
          width: '200px',
          display: 'flex',
          flexDirection: 'column',
          paddingRight: '10px',
          height: `${barsAreaHeight}px`
        }}>
          {data.map((item, index) => {
            const isHovered = hoveredBar === item.title;
            return (
              <div 
                key={`label-${index}`} 
                style={{
                  height: `${barHeight}px`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'flex-end',
                  marginBottom: index < data.length - 1 ? `${barGap}px` : '0px',
                  fontSize: '12px',
                  fontWeight: isHovered ? 'bold' : 'normal',
                  color: isHovered ? '#1CC53C' : 'inherit'
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
          style={{ flexGrow: 1, position: 'relative', height: `${totalChartHeight}px` }}
        >
          {/* Линия оси Y */}
          <div style={{
            position: 'absolute',
            left: '0',
            top: '0',
            height: `${barsAreaHeight}px`,
            width: '1px',
            background: '#333',
            zIndex: 2
          }}></div>

          {/* Контейнер столбцов */}
          <div style={{ 
            height: `${barsAreaHeight}px`,
            display: 'flex',
            flexDirection: 'column'
          }}>
            {data.map((item, index) => {
              const isHovered = hoveredBar === item.title;
              
              // Ширина всей полосы в пикселях
              const barTotalWidth = containerWidth * (item.total / maxValue);
              
              // Расчет ширины для всех сегментов
              const segmentWidths = calculateSegmentWidths(item.segments, item.total, barTotalWidth);
              
              return (
                <div 
                  key={`bar-${index}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    height: `${barHeight}px`,
                    marginBottom: index < data.length - 1 ? `${barGap}px` : '0px',
                    cursor: 'pointer',
                    opacity: isHovered ? 0.9 : 1,
                    transform: isHovered ? 'translateX(2px)' : 'none',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={() => handleBarHover(item.title)}
                  onMouseLeave={() => handleBarHover(null)}
                  title={isHovered ? `Всего: ${item.total} дел` : ''}
                >
                  <div style={{
                    flexGrow: 1,
                    height: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    background: 'rgba(0, 0, 0, 0.05)',
                    borderRadius: '4px',
                    overflow: 'hidden',
                    position: 'relative'
                  }}>
                    {/* Сегментированный столбец */}
                    <div style={{
                      height: '100%',
                      width: `${(item.total / maxValue) * 100}%`,
                      display: 'flex',
                      borderRadius: '5px',
                      overflow: 'visible', 
                      border: '1px solid #ccc',
                      boxShadow: isHovered ? '0 0 8px rgba(0,0,0,0.3)' : 'none'
                    }}>
                      {item.segments.map((segment, segIndex) => {
                        if (segment.value === 0) return null;
                        
                        const isSegmentClickable = segment.value > 0 && onSegmentClick;
                        
                        return (
                          <div
                            key={segIndex}
                            style={{
                              width: segmentWidths[segIndex],
                              height: '100%',
                              backgroundColor: segment.color,
                              borderRight: segIndex < item.segments.length - 1 ? '1px solid #fff' : 'none',
                              flexShrink: 0,
                              minWidth: '2px',
                              cursor: isSegmentClickable ? 'pointer' : 'default'
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
          <div style={{
            position: 'absolute',
            top: `${barsAreaHeight}px`,
            left: '0',
            right: '0',
            height: `${xAxisHeight}px`,
            borderTop: '1px solid #333'
          }}>
            {xTicks.map(tick => (
              <div 
                key={`tick-${tick}`}
                style={{
                  position: 'absolute',
                  bottom: '0',
                  left: `${(tick / maxValue) * 100}%`,
                  transform: 'translateX(-50%)',
                  textAlign: 'center'
                }}
              >
                <div style={{
                  height: '5px',
                  width: '1px',
                  background: '#333',
                  margin: '0 auto'
                }}></div>
                <div style={{
                  fontSize: '12px',
                  color: '#666',
                  marginTop: '3px'
                }}>
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