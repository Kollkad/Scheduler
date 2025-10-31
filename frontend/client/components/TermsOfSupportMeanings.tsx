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
    <div className="terms-meanings">
      {legendItems.map((item, index) => (
        <div key={index} className="legend-item">
          <div
            className="legend-color"
            style={{ backgroundColor: item.color }}
          ></div>
          <div className="legend-text">
            <span className="color-name">{item.label}</span>
            <span className="separator"> – </span>
            <span>{item.description}</span>
          </div>
        </div>
      ))}

      <style jsx>{`
        .terms-meanings {
          padding: 20px;
          background: white;
          border-radius: 20px;
          border: 2px solid #1CC53C;
          width: 100%;
        }

        .legend-item {
          display: flex;
          align-items: flex-start;
          margin-bottom: 12px;
          font-size: 14px;
          line-height: 1.4;
        }

        .legend-item:last-child {
          margin-bottom: 0;
        }

        .legend-color {
          width: 16px;
          height: 16px;
          border-radius: 3px;
          margin-right: 8px;
          margin-top: 1px;
          flex-shrink: 0;
        }

        .legend-text {
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