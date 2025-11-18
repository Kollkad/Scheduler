// TermsOfSupportMeanings.tsx
interface LegendItem {
  color: string;
  label: string;
  description: string;
}

// Конфигурация легенды для цветовой системы сроков сопровождения дел
const legendItems: LegendItem[] = [
  {
    color: '#8e8e8e',
    label: 'Серый',
    description: 'Недостаточно информации для определения сроков сопровождения или не попадает под фильтры'
  },
  {
    color: '#41A457', 
    label: 'Зеленый',
    description: 'Дело обрабатывается как ожидается'
  },
  {
    color: '#FF5e3e',
    label: 'Красный',
    description: 'Дело просрочено'
  },
  {
    color: '#6EDFF2',
    label: 'Голубой',
    description: 'Дело переоткрыто'
  },
  {
    color: '#3d3dff',
    label: 'Синий',
    description: 'Жалоба подана'
  },
  {
    color: '#e65cb3',
    label: 'Розовый',
    description: 'Ошибка дубликат'
  },
  {
    color: '#8b00ff',
    label: 'Фиолетовый',
    description: 'Отозвано инициатором'
  }
];

export function TermsOfSupportMeanings() {
  return (
    <div className="p-5 bg-white rounded-2xl border-2 border-green-500 w-full">
      {legendItems.map((item, index) => (
        <div key={index} className="flex items-start mb-3 text-sm leading-relaxed">
          <div
            className="w-4 h-4 rounded-sm mr-2 mt-0.5 flex-shrink-0"
            style={{ backgroundColor: item.color }}
          ></div>
          <div className="flex-1 text-gray-800">
            <span className="font-bold">{item.label}</span>
            <span className="text-gray-800"> – </span>
            <span>{item.description}</span>
          </div>
        </div>
      ))}
    </div>
  );
}