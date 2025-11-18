// DefaultChart.tsx
import { useMemo, useState } from 'react';
import { calculateBarHeights, generateTicks } from '@/utils/chartUtils';

interface DefaultChartProps {
  data: { label: string; value: number; color: string }[];
  onBarClick?: (item: { label: string; value: number; color: string }) => void;
}

export function DefaultChart({ data, onBarClick }: DefaultChartProps) {
  const [hoveredBar, setHoveredBar] = useState<string | null>(null);

  const { maxValue, tickStep } = useMemo(() => {
    const maxVal = Math.max(...data.map(item => item.value), 1);
    
    let step;
    if (maxVal <= 12000) {
      step = 1000;
    } else {
      step = 3000;
    }
    
    const roundedMax = Math.ceil(maxVal / step) * step;
    
    return { maxValue: roundedMax, tickStep: step };
  }, [data]);

  const calculateWidth = (value: number) => {
    if (value === 0) return 0;
    const calculatedWidth = (value / maxValue) * 100;
    return calculatedWidth < 0.5 ? 0.5 : calculatedWidth;
  };

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

  const { barHeight, barGap, barsAreaHeight, xAxisHeight, totalChartHeight } = 
    calculateBarHeights(data.length);
  
  const xTicks = generateTicks(maxValue, tickStep);

  const handleBarClick = (item: { label: string; value: number; color: string }) => {
    if (item.value > 0 && onBarClick) {
      onBarClick(item);
    }
  };

  const handleBarHover = (label: string | null) => {
    setHoveredBar(label);
  };

  return (
    <div className="w-full max-w-[800px] mx-auto p-4 bg-white rounded-md shadow-sm pb-12">
      <div className="flex">
        <div className="w-24 flex flex-col pr-2">
          {data.map((item, index) => (
            <div
              key={`label-${index}`}
              className={`flex items-center justify-end text-sm ${
                hoveredBar === item.label ? 'font-bold text-green-500' : ''
              }`}
              style={{
                height: `${barHeight}px`,
                marginBottom: index < data.length - 1 ? `${barGap}px` : '0px'
              }}
            >
              {item.label}
            </div>
          ))}
        </div>

        <div className="flex-grow">
          <div className="flex" style={{ height: `${barsAreaHeight}px` }}>
            {/* Ось Y */}
            <div 
              className="bg-gray-800"
              style={{
                height: '100%',
                width: '1px'
              }}
            ></div>
            
            {/* Область столбцов */}
            <div className="flex-grow flex flex-col ">
              {data.map((item, index) => {
                const width = calculateWidth(item.value);
                const isHovered = hoveredBar === item.label;
                const isClickable = item.value > 0 && onBarClick;
                
                return (
                  <div
                    key={`bar-${index}`}
                    className={`flex items-center transition-all duration-200 ${
                      isClickable ? 'cursor-pointer' : 'cursor-default'
                    } ${isHovered ? 'opacity-90 translate-x-0.5' : ''}`}
                    style={{
                      height: `${barHeight}px`,
                      marginBottom: index < data.length - 1 ? `${barGap}px` : '0px'
                    }}
                    onClick={() => handleBarClick(item)}
                    onMouseEnter={() => handleBarHover(item.label)}
                    onMouseLeave={() => handleBarHover(null)}
                    title={isClickable ? `Нажмите чтобы посмотреть ${item.value} дел` : 'Нет дел'}
                  >
                    <div className="flex-grow h-full flex items-center bg-gray-100 rounded-lg overflow-hidden relative">
                      {width > 0 && (
                        <div
                          className="h-full rounded-lg flex items-center justify-end pr-2 box-border transition-all duration-500 shadow-sm"
                          style={{
                            width: `${width}%`,
                            backgroundColor: item.color,
                            border: `1px solid ${getDarkerColor(item.color)}`,
                            minWidth: '20px',
                            boxShadow: isHovered ? '0 0 8px rgba(0,0,0,0.3)' : 'none'
                          }}
                        />
                      )}
                      <span className="text-sm font-bold text-black absolute right-1">
                        {item.value}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Ось X */}
          <div 
            className="border-t border-gray-800 relative"
            style={{
              height: `${xAxisHeight}px`
            }}
          >
            {xTicks.map(tick => (
              <div
                key={`tick-${tick}`}
                className="absolute bottom-0 text-center"
                style={{
                  left: `${(tick / maxValue) * 100}%`,
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