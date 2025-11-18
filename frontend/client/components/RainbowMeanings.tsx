// RainbowMeanings.tsx
interface RainbowMeaning {
  color: string;
  colorName: string;
  text: string;
}

// Конфигурация цветов и их значений для системы мониторинга дел
const rainbowMeanings: RainbowMeaning[] = [
  {
    color: '#000000',
    colorName: 'ИК',
    text: 'Ипотечные кредиты.'
  },
  {
    color: '#8e8e8e', 
    colorName: 'Серый',
    text: 'выделены дела со статусом «Переоткрыто».'
  },
  {
    color: '#41A457',
    colorName: 'Зеленый', 
    text: 'выделены дела со статусом «Суд акт вступил в законную силу» и имеют «Фактическую дату передачи ИД в ПСИП».'
  },
  {
    color: '#ffe947',
    colorName: 'Желтый',
    text: 'выделены дела со статусом «Условно закрыто» и имеют «Фактическую дату передачи».'
  },
  {
    color: '#FFA73B',
    colorName: 'Оранжевый',
    text: 'выделены дела со статусом «Суд акт вступил в законную силу», без «Фактической даты передачи».'
  },
  {
    color: '#3d3dff',
    colorName: 'Синий',
    text: 'выделены дела «Приказное производство» в работе свыше 90 дней в работе.'
  },
  {
    color: '#FF5e3e',   
    colorName: 'Красный',
    text: 'выделены неотработанные дела, поступившие в работу до 2023 года.'
  },
  {
    color: '#D53DFF',    
    colorName: 'Лиловый',
    text: 'выделены дела «Исковое производство» в работе свыше 120 дней в работе.'
  },
  {
    color: '#FFFFFF',
    colorName: 'Белый',
    text: 'для мониторинга и отработки в рабочем порядке.'
  }
];

export function RainbowMeanings() {
  return (
    <div className="p-5 bg-white rounded-2xl border-2 border-green-500 w-full">
      {rainbowMeanings.map((meaning, index) => (
        <div key={index} className="flex items-start mb-3 text-sm leading-relaxed">
          <div
            className="w-4 h-4 rounded-sm mr-2 mt-0.5 flex-shrink-0"
            style={{
              backgroundColor: meaning.color,
              border: meaning.color === '#FFFFFF' ? '1px solid #ccc' : 'none'
            }}
          ></div>
          <div className="flex-1 text-gray-800">
            <span className="font-bold">{meaning.colorName}</span>
            <span className="text-gray-800"> – </span>
            <span>{meaning.text}</span>
          </div>
        </div>
      ))}
    </div>
  );
}