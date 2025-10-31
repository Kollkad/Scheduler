// RadioButtonGroup.tsx
interface RadioOption {
  id: string;
  label: string;
  value: string;
}

interface RadioButtonGroupProps {
  options: RadioOption[];
  value?: string;
  onChange?: (value: string) => void;
  name: string;
}

export function RadioButtonGroup({ options, value, onChange, name }: RadioButtonGroupProps) {
  // Функция обрабатывает изменение выбранной опции
  const handleChange = (value: string) => {
    onChange?.(value);
  };

  return (
    <div className="space-y-4">
      {options.map((option) => (
        <div 
          key={option.id}
          className="flex items-start space-x-3 p-4 bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-colors cursor-pointer"
          onClick={() => handleChange(option.value)}
        >
          <div className="flex items-center h-5">
            <input
              id={option.id}
              name={name}
              type="radio"
              value={option.value}
              checked={value === option.value} 
              onChange={() => handleChange(option.value)}
              className="h-4 w-4 border-gray-300 text-green-600 focus:ring-green-500 cursor-pointer"
              style={{ accentColor: '#1CC53C' }}
            />
          </div>
          <label 
            htmlFor={option.id}
            className="text-sm font-medium text-gray-900 cursor-pointer leading-5"
          >
            {option.label}
          </label>
        </div>
      ))}
    </div>
  );
}