// SorterTypes.ts
export interface SelectOption {
  value: string;
  label: string;
}

export interface SorterField {
  id: string;
  placeholder: string;
  hasSearch?: boolean;
  isSelected?: boolean;
  options: SelectOption[];
  // Поля для динамической загрузки опций
  endpoint?: string; // API endpoint для загрузки опций
  dependsOn?: string; // Поле, от которого зависит этот селект
}

export interface SorterButton {
  type: 'primary' | 'secondary';
  text: string;
  onClick?: () => void;
}

export interface SorterFormProps {
  title: string;
  fields: SorterField[];
  buttons: SorterButton[];
  additionalFiltersButton?: boolean;
  onFiltersChange?: (filters: Record<string, string>) => void;
}

export interface SmartSelectProps {
  placeholder: string;
  options: SelectOption[];
  hasSearch?: boolean;
  value?: string;
  onValueChange?: (value: string) => void;
  onClear?: () => void;
  isSelected?: boolean;
  isLoading?: boolean;
  onSearch?: (searchTerm: string) => void;
  endpoint?: string; 
}