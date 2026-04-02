// AnalysisProgress.tsx
interface AnalysisProgressProps {
  isOpen: boolean;
  progress: number;
  currentStep: string;
  onCancel: () => void;
}

export function AnalysisProgress({ isOpen, progress, currentStep, onCancel }: AnalysisProgressProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-bg-medium-gray flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-96 border border-border-default">
        <h3 className="text-lg font-semibold text-text-primary mb-4">Анализ данных</h3>
        
        <div className="w-full bg-bg-default-light-field rounded-full h-2 mb-4">
          <div 
            className="bg-green h-2 rounded-full transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
        
        <p className="text-sm text-text-secondary mb-4">{currentStep}</p>
        <p className="text-xs text-text-tertiary mb-4">Это может занять несколько минут...</p>
        
        <button
          onClick={onCancel}
          className="text-red-default text-sm hover:text-red-transparent"
        >
          Отменить анализ
        </button>
      </div>
    </div>
  );
}