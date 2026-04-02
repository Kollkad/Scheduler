// client/utils/dateFormat.ts

export const formatDate = (value: string | Date | null | undefined): string => {
  if (!value) return '—';
  
  try {
    let year: number, month: number, day: number;
    
    if (value instanceof Date) {
      year = value.getFullYear();
      month = value.getMonth() + 1;
      day = value.getDate();
    } else if (typeof value === 'string') {
      const cleanString = value.trim();
      
      // Формат: 2026-02-04 или 2026-02-04T00:00:00
      const isoMatch = cleanString.match(/^(\d{4})-(\d{2})-(\d{2})/);
      if (isoMatch) {
        year = parseInt(isoMatch[1]);
        month = parseInt(isoMatch[2]);
        day = parseInt(isoMatch[3]);
      } else {
        // Формат: 04.02.2026 или 04/02/2026
        const ruMatch = cleanString.match(/^(\d{2})[.\/](\d{2})[.\/](\d{4})/);
        if (ruMatch) {
          day = parseInt(ruMatch[1]);
          month = parseInt(ruMatch[2]);
          year = parseInt(ruMatch[3]);
        } else {
          return '—';
        }
      }
    } else {
      return '—';
    }
    
    // Валидация диапазонов
    if (year < 1000 || year > 9999) return '—';
    if (month < 1 || month > 12) return '—';
    if (day < 1 || day > 31) return '—';
    
    // Форматирование в ДД.ММ.ГГГГ
    const formattedDay = String(day).padStart(2, '0');
    const formattedMonth = String(month).padStart(2, '0');
    
    return `${formattedDay}.${formattedMonth}.${year}`;
  } catch {
    return '—';
  }
};