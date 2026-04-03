// client/pages/UserProfileDetail.tsx

import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Loader } from "lucide-react";
import { PageContainer } from "@/components/PageContainer";
import { Button } from "@/components/ui/button";
import { apiClient } from '@/services/api/client';
import { API_ENDPOINTS } from '@/services/api/endpoints';
import { TaskCardList } from "@/components/TaskCardList";
import { DefaultChart } from "@/components/DefaultChart";
import { Task } from "@/services/api/taskTypes";

interface UserInfo {
  login: string;
  email: string;
  name: string;
  role: string;
}

export function UserProfileDetail() {
  const navigate = useNavigate();
  const [user, setUser] = useState<UserInfo | null>(null);
  const [userLoading, setUserLoading] = useState(true);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [tasksLoading, setTasksLoading] = useState(true);

  // Загрузка данных пользователя
  useEffect(() => {
    apiClient.get<UserInfo>(API_ENDPOINTS.USER_INFO)
      .then(data => {
        setUser(data);
        setUserLoading(false);
      })
      .catch(() => setUserLoading(false));
  }, []);

  // Загрузка задач пользователя после получения данных о пользователе
  useEffect(() => {
    if (user?.name) {
      setTasksLoading(true);
      const filters = {
        responsibleExecutor: user.name
      };
      apiClient.get<{ success: boolean; tasks: Task[]; filteredCount: number }>(
        `${API_ENDPOINTS.TASKS_LIST}?filters=${encodeURIComponent(JSON.stringify(filters))}`
      )
        .then(response => {
          if (response?.success && response.tasks) {
            setTasks(response.tasks);
          } else {
            setTasks([]);
          }
        })
        .catch(() => setTasks([]))
        .finally(() => setTasksLoading(false));
    }
  }, [user?.name]);

  // Подготовка данных для диаграммы: группировка задач по тексту задачи
  const chartData = useMemo(() => {
    if (!tasks.length) return [];

    // Подсчет количества задач по каждому уникальному тексту
    const taskCountMap = new Map<string, number>();
    tasks.forEach(task => {
      const taskText = task.taskText || "Без названия";
      taskCountMap.set(taskText, (taskCountMap.get(taskText) || 0) + 1);
    });

    // Преобразование в массив для сортировки
    let items = Array.from(taskCountMap.entries()).map(([label, value]) => ({
      label: label, 
      value,
      color: "#86efac" // bg-light-green
    }));

    // Сортировка по убыванию количества
    items.sort((a, b) => b.value - a.value);

    // Если больше 10 типов задач, останется топ-9 + "Остальные"
    if (items.length > 10) {
      const topItems = items.slice(0, 9);
      const otherValue = items.slice(9).reduce((sum, item) => sum + item.value, 0);
      
      items = [
        ...topItems,
        { label: "Остальные", value: otherValue, color: "#86efac" }
      ];
    }

    return items;
  }, [tasks]);

  // Обработчик клика по столбцу диаграммы
  const handleBarClick = (item: { label: string; value: number; color: string }) => {
    if (item.label === "Остальные") {
      // Для "Остальных" показать все задачи или ничего не делать
      return;
    }
    
    // Фильтрация задач по тексту и сохранение в state для отображения
    const filteredTasks = tasks.filter(task => 
      (task.taskText || "Без названия").startsWith(item.label.replace("...", ""))
    );
    
    // Можно открыть модалку или обновить список
    console.log("Задачи по типу:", filteredTasks);
    //мб будет логика отфильтрованных задач TODO
  };

  if (userLoading || tasksLoading) {
    return (
      <PageContainer>
        <div className="flex items-center justify-center h-64">
          <Loader className="h-8 w-8 animate-spin text-blue" />
        </div>
      </PageContainer>
    );
  }

  if (!user) {
    return (
      <PageContainer>
        <div className="text-center text-red py-8">
          Не удалось загрузить данные пользователя
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      {/* Кнопка назад */}
      <div className="mb-6">
        <Button 
          variant="grayOutline"
          size="rounded"
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Вернуться назад
        </Button>
      </div>

      {/* Информация о пользователе */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text-primary">
          {user.role}: {user.name}
        </h1>
        <p className="text-sm text-text-secondary mt-1">
          {user.email}
        </p>
      </div>

      {/* Разделитель */}
      <hr className="border-border my-6" />

      {/* Заголовок секции задач */}
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-text-primary">
          Задачи пользователя
        </h2>
        <p className="text-sm text-text-secondary">
          Всего задач: {tasks.length}
        </p>
      </div>

      {/* Диаграмма распределения задач */}
      {chartData.length > 0 && (
        <div className="mb-8">
          <DefaultChart 
            data={chartData} 
            onBarClick={handleBarClick}
          />
        </div>
      )}

      {/* Заголовок списка задач */}
      <div className="mt-8 mb-4">
        <h2 className="text-lg font-semibold text-text-primary">
          Список задач
        </h2>
      </div>

      {/* Список задач в виде карточек */}
      {tasks.length > 0 ? (
        <TaskCardList tasks={tasks} />
      ) : (
        <div className="text-center text-text-secondary py-8">
          У пользователя нет задач
        </div>
      )}
    </PageContainer>
  );
}

export default UserProfileDetail;