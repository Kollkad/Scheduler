// client/components/profile/profileConfig.ts

// Иерархия ролей: чем выше число, тем больше прав
export const roleHierarchy: Record<string, number> = {
  "Администратор": 4,
  "Руководитель": 3,
  "Сотрудник": 2,
  "Гость": 1,
};

// Интерфейс вкладки профиля
export interface ProfileTab {
  id: string;
  label: string;
  minRole: string;  // минимальная роль для отображения вкладки
}

// Конфигурация вкладок профиля
export const profileTabs: ProfileTab[] = [
  {
    id: "tasks",
    label: "Мои задачи",
    minRole: "Сотрудник",
  },
  {
    id: "reports",
    label: "Репорты",
    minRole: "Администратор",
  },
];

// Проверяет, доступна ли вкладка для указанной роли
export const isTabVisible = (tab: ProfileTab, userRole: string): boolean => {
  const userLevel = roleHierarchy[userRole] || 0;
  const minLevel = roleHierarchy[tab.minRole] || 0;
  return userLevel >= minLevel;
};
