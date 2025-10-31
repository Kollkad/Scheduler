export const calculateBarHeights = (
  dataLength: number, 
  barHeight: number = 32, 
  barGap: number = 8,
  xAxisHeight: number = 30
) => {
  const barsAreaHeight = dataLength * barHeight + (dataLength - 1) * barGap;
  const totalChartHeight = barsAreaHeight + xAxisHeight;
  
  return { barHeight, barGap, barsAreaHeight, xAxisHeight, totalChartHeight };
};

export const generateTicks = (maxValue: number, tickStep: number = 1000) => {
  return Array.from(
    { length: Math.floor(maxValue / tickStep) + 1 },
    (_, i) => i * tickStep
  );
};