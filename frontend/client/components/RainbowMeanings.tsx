// RainbowMeanings.tsx
interface RainbowMeaning {
  colorClass: string;
  colorName: string;
  text: string;
}

const rainbowMeanings: RainbowMeaning[] = [
  { colorClass: 'bg-black', colorName: 'ИК', text: 'Ипотечные кредиты.' },
  { colorClass: 'bg-diagram-gray', colorName: 'Серый', text: 'выделены дела со статусом «Переоткрыто».' },
  { colorClass: 'bg-green-semi-dark', colorName: 'Зеленый', text: 'выделены дела со статусом «Суд акт вступил в законную силу» и имеют «Фактическую дату передачи ИД в ПСИП».' },
  { colorClass: 'bg-yellow', colorName: 'Желтый', text: 'выделены дела со статусом «Условно закрыто» и имеют «Фактическую дату передачи».' },
  { colorClass: 'bg-diagram-orange', colorName: 'Оранжевый', text: 'выделены дела со статусом «Суд акт вступил в законную силу», без «Фактической даты передачи».' },
  { colorClass: 'bg-diagram-blue', colorName: 'Синий', text: 'выделены дела «Приказное производство» в работе свыше 90 дней в работе.' },
  { colorClass: 'bg-diagram-red', colorName: 'Красный', text: 'выделены неотработанные дела, поступившие в работу до 2025 года.' },
  { colorClass: 'bg-diagram-purple', colorName: 'Лиловый', text: 'выделены дела «Исковое производство» в работе свыше 120 дней в работе.' },
  { colorClass: 'bg-white border border-border-default', colorName: 'Белый', text: 'для мониторинга и отработки в рабочем порядке.' }
];

export function RainbowMeanings() {
  return (
    <div className="p-5 bg-white rounded-2xl border border-green-dark w-full">
      {rainbowMeanings.map((meaning, index) => (
        <div key={index} className="flex items-start mb-3 text-sm leading-relaxed">
          <div className={`w-4 h-4 rounded-sm mr-2 mt-0.5 flex-shrink-0 ${meaning.colorClass}`}></div>
          <div className="flex-1 text-text-primary">
            <span className="font-bold">{meaning.colorName}</span>
            <span className="text-text-primary"> – </span>
            <span>{meaning.text}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
