// DefaultChart.tsx
import { useMemo, useState } from 'react';
import { calculateBarHeights, generateTicks } from '@/utils/chartUtils';

interface DefaultChartProps {
  data: { label: string; value: number; color: string }[];
  onBarClick?: (item: { label: string; value: number; color: string }) => void;
}

export function DefaultChart({ data, onBarClick }: DefaultChartProps) {
  const [hoveredBar, setHoveredBar] = useState<string | null>(null);

  // Функция вычисляет максимальное значение и шаг для шкалы
  const { maxValue, tickStep } = useMemo(() => {
    const maxVal = Math.max(...data.map(item => item.value), 1);
    const step = Math.ceil(maxVal / 5 / 1000) * 1000;
    return { maxValue: maxVal, tickStep: step };
  }, [data]);

  // Функция рассчитывает ширину столбца на основе значения
  const calculateWidth = (value: number) => {
    if (value === 0) return 0;
    const calculatedWidth = (value / maxValue) * 100;
    return calculatedWidth < 0.5 ? 0.5 : calculatedWidth;
  };

  // Функция создает затемненную версию цвета для границ
  const getDarkerColor = (hex: string) => {
    let r = parseInt(hex.substring(1, 3), 16);
    let g = parseInt(hex.substring(3, 5), 16);
    let b = parseInt(hex.substring(5, 7), 16);

    r = Math.floor(r * 0.8);
    g = Math.floor(g * 0.8);
    b = Math.floor(b * 0.8);

    const rHex = r.toString(16).padStart(2, '0');
    const gHex = g.toString(16).padStart(2, '0');
    const bHex = b.toString(16).padStart(2, '0');

    return `#${rHex}${gHex}${bHex}`;
  };

  // Расчет размеров элементов графика
  const { barHeight, barGap, barsAreaHeight, xAxisHeight, totalChartHeight } = 
    calculateBarHeights(data.length);
  
  // Генерация меток для оси X
  const xTicks = generateTicks(maxValue, tickStep);

  // Обработчик клика по столбцу
  const handleBarClick = (item: { label: string; value: number; color: string }) => {
    if (item.value > 0 && onBarClick) {
      onBarClick(item);
    }
  };

  // Обработчик наведения на столбец
  const handleBarHover = (label: string | null) => {
    setHoveredBar(label);
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
        {/* Контейнер для подписей оси Y */}
        <div style={{
          width: '100px',
          display: 'flex',
          flexDirection: 'column',
          paddingRight: '10px',
          height: `${barsAreaHeight}px`
        }}>
          {data.map((item, index) => (
            <div
              key={`label-${index}`}
              style={{
                height: `${barHeight}px`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-end',
                marginBottom: index < data.length - 1 ? `${barGap}px` : '0px',
                fontSize: '12px',
                fontWeight: hoveredBar === item.label ? 'bold' : 'normal',
                color: hoveredBar === item.label ? '#1CC53C' : 'inherit'
              }}
            >
              {item.label}
            </div>
          ))}
        </div>

        {/* Область графика */}
        <div style={{ flexGrow: 1, position: 'relative', height: `${totalChartHeight}px` }}>
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

          {/* Контейнер для столбцов */}
          <div style={{
            height: `${barsAreaHeight}px`,
            display: 'flex',
            flexDirection: 'column'
          }}>
            {data.map((item, index) => {
              const width = calculateWidth(item.value);
              const isHovered = hoveredBar === item.label;
              const isClickable = item.value > 0 && onBarClick;
              
              return (
                <div
                  key={`bar-${index}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    height: `${barHeight}px`,
                    marginBottom: index < data.length - 1 ? `${barGap}px` : '0px',
                    cursor: isClickable ? 'pointer' : 'default',
                    opacity: isHovered ? 0.9 : 1,
                    transform: isHovered ? 'translateX(2px)' : 'none',
                    transition: 'all 0.2s ease'
                  }}
                  onClick={() => handleBarClick(item)}
                  onMouseEnter={() => handleBarHover(item.label)}
                  onMouseLeave={() => handleBarHover(null)}
                  title={isClickable ? `Нажмите чтобы посмотреть ${item.value} дел` : 'Нет дел'}
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
                    {/* Цветная часть столбца */}
                    {width > 0 && (
                      <div
                        style={{
                          height: '100%',
                          width: `${width}%`,
                          backgroundColor: item.color,
                          border: `1px solid ${getDarkerColor(item.color)}`,
                          borderRadius: '5px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'flex-end',
                          paddingRight: '10px',
                          boxSizing: 'border-box',
                          transition: 'width 0.5s ease',
                          minWidth: '20px',
                          boxShadow: isHovered ? '0 0 8px rgba(0,0,0,0.3)' : 'none'
                        }}
                      />
                    )}
                    {/* Числовое значение */}
                    <span style={{
                      fontSize: '12px',
                      fontWeight: 'bold',
                      color: 'black',
                      marginLeft: '5px',
                      position: 'absolute',
                      right: '5px'
                    }}>
                      {item.value}
                    </span>
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