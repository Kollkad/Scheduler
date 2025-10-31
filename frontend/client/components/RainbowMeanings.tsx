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
    <div className="color-meanings">
      {rainbowMeanings.map((meaning, index) => (
        <div key={index} className="meaning-item">
          <div
            className="meaning-color"
            style={{
              backgroundColor: meaning.color,
              border: meaning.color === '#FFFFFF' ? '1px solid #ccc' : 'none'
            }}
          ></div>
          <div className="meaning-text">
            <span className="color-name">{meaning.colorName}</span>
            <span className="separator"> – </span>
            <span>{meaning.text}</span>
          </div>
        </div>
      ))}

      <style jsx>{`
        .color-meanings {
          padding: 20px;
          background: white;
          border-radius: 20px;
          border: 2px solid #1CC53C;
          width: 100%;
        }

        .meaning-item {
          display: flex;
          align-items: flex-start;
          margin-bottom: 12px;
          font-size: 14px;
          line-height: 1.4;
        }

        .meaning-item:last-child {
          margin-bottom: 0;
        }

        .meaning-color {
          width: 16px;
          height: 16px;
          border-radius: 3px;
          margin-right: 8px;
          margin-top: 1px;
          flex-shrink: 0;
        }

        .meaning-text {
          flex: 1;
          color: #333;
        }

        .color-name {
          font-weight: bold;
        }

        .separator {
          color: #333;
        }
      `}</style>
    </div>
  );
}