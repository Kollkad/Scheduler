// TermsOfSupportMeanings.tsx
interface LegendItem {
  colorClass: string;
  label: string;
  description: string;
}

const legendItems: LegendItem[] = [
  { colorClass: 'bg-diagram-gray', label: 'Серый', description: 'Недостаточно информации для определения сроков сопровождения или не попадает под фильтры' },
  { colorClass: 'bg-green-semi-dark', label: 'Зеленый', description: 'Дело обрабатывается как ожидается' },
  { colorClass: 'bg-diagram-red', label: 'Красный', description: 'Дело просрочено' },
  { colorClass: 'bg-diagram-cyan', label: 'Голубой', description: 'Дело переоткрыто' },
  { colorClass: 'bg-diagram-blue', label: 'Синий', description: 'Жалоба подана' },
  { colorClass: 'bg-diagram-pink', label: 'Розовый', description: 'Ошибка дубликат' },
  { colorClass: 'bg-diagram-violet', label: 'Фиолетовый', description: 'Отозвано инициатором' }
];

export function TermsOfSupportMeanings() {
  return (
    <div className="p-5 bg-white rounded-2xl border border-green-dark w-full">
      {legendItems.map((item, index) => (
        <div key={index} className="flex items-start mb-3 text-sm leading-relaxed">
          <div className={`w-4 h-4 rounded-sm mr-2 mt-0.5 flex-shrink-0 ${item.colorClass}`}></div>
          <div className="flex-1 text-text-primary">
            <span className="font-bold">{item.label}</span>
            <span className="text-text-primary"> – </span>
            <span>{item.description}</span>
          </div>
        </div>
      ))}
    </div>
  );
}