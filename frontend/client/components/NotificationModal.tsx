// NotificationModal.tsx
import { useState, useEffect, useRef } from "react";
import { X, Copy } from "lucide-react";

interface NotificationModalProps {
  isOpen: boolean;
  onClose: () => void;
  caseCode: string;
  employeeName: string;
  caseStatus: string;
  observationStatus: string;
}

export function NotificationModal({
  isOpen,
  onClose,
  caseCode,
  employeeName,
  caseStatus,
  observationStatus
}: NotificationModalProps) {
  const [showCopySuccess, setShowCopySuccess] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);

  // Функция генерирует критерии наблюдения на основе статуса
  const getObservationCriteria = (status: string) => {
    switch (status.toLowerCase()) {
      case 'просрочено':
        return 'Превышен установленный срок рассмотрения дела';
      case 'в срок':
        return 'Дело находится в установленных временных рамках';
      default:
        return 'Требуется уточнение статуса';
    }
  };

  // Функция определяет рекомендуемые действия в зависимости от статуса
  const getRecommendedAction = (status: string) => {
    switch (status.toLowerCase()) {
      case 'просрочено':
        return 'Рекомендуется незамедлительно принять меры по ускорению рассмотрения дела и предоставить обновленную информацию о ходе процесса.';
      case 'в срок':
        return 'Продолжайте отслеживать ход дела согласно установленному графику.';
      default:
        return 'Просьба предоставить актуальную информацию о статусе дела.';
    }
  };

  // Текст уведомления для копирования
  const messageText = `Уважаемый(ая) ${employeeName},
дело ${caseCode} (${caseStatus}) требует вашего внимания.

Текущий статус наблюдения:
🔹 ${observationStatus}
🔹 Причина: ${getObservationCriteria(observationStatus)}

${getRecommendedAction(observationStatus)}`;

  // Функция копирует текст в буфер обмена с использованием разных методов
  const handleCopy = async () => {
    try {
      // Использование современного Clipboard API
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(messageText);
        setShowCopySuccess(true);
        setTimeout(() => setShowCopySuccess(false), 5000);
        return;
      }

      // Резервный метод для сред, где Clipboard API заблокирован
      const textArea = document.createElement('textarea');
      textArea.value = messageText;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();

      const successful = document.execCommand('copy');
      document.body.removeChild(textArea);

      if (successful) {
        setShowCopySuccess(true);
        setTimeout(() => setShowCopySuccess(false), 5000);
      } else {
        throw new Error('Copy command failed');
      }
    } catch (err) {
      console.error('Failed to copy text: ', err);
      setShowCopySuccess(true);
      setTimeout(() => setShowCopySuccess(false), 5000);
    }
  };

  // Обработчик клика вне модального окна для его закрытия
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  // Обработчик нажатия клавиши Escape для закрытия модального окна
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div 
        ref={modalRef}
        className="bg-white rounded-2xl p-6 max-w-2xl w-full relative"
        style={{
          border: '1px solid #BDBDCC',
          boxShadow: '2px 4px 8px rgba(0, 0, 0, 0.1), -2px 0 8px rgba(0, 0, 0, 0.05)'
        }}
      >
        {/* Кнопка закрытия */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 hover:bg-gray-100 rounded-full transition-colors"
        >
          <X className="h-5 w-5" style={{ color: '#1F1F1F' }} />
        </button>

        {/* Заголовок */}
        <h2 className="text-xl font-semibold text-gray-900 mb-6 pr-8">
          Уведомление сотруднику
        </h2>

        {/* Содержимое сообщения */}
        <div className="bg-gray-50 rounded-lg p-6 mb-6">
          <pre className="whitespace-pre-wrap text-sm text-gray-900 font-sans leading-relaxed">
            {messageText}
          </pre>
        </div>

        {/* Кнопка копирования */}
        <div className="flex justify-end">
          <button
            onClick={handleCopy}
            className="inline-flex items-center px-6 py-2 text-sm font-medium text-white rounded-full transition-colors"
            style={{ backgroundColor: '#1CC53C' }}
          >
            <Copy className="h-4 w-4 mr-2" />
            Копировать
          </button>
        </div>

        {/* Сообщение об успешном копировании */}
        {showCopySuccess && (
          <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2">
            <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-2 rounded-lg text-sm">
              Текст успешно скопирован!
            </div>
          </div>
        )}
      </div>
    </div>
  );
}