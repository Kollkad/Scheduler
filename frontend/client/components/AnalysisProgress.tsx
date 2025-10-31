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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-96">
        <h3 className="text-lg font-semibold mb-4">Анализ данных</h3>
        
        <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
          <div 
            className="bg-green-600 h-2 rounded-full transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
        
        <p className="text-sm text-gray-600 mb-4">{currentStep}</p>
        <p className="text-xs text-gray-500 mb-4">Это может занять несколько минут...</p>
        
        <button
          onClick={onCancel}
          className="text-red-600 text-sm hover:text-red-800"
        >
          Отменить анализ
        </button>
      </div>
    </div>
  );
}