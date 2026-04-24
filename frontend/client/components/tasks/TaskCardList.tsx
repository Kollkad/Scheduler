// frontend/client/components/tasks/TaskCardList.tsx

import { TaskCard } from "@/components/tasks/TaskCard";
import { Task } from "@/services/api/taskTypes";

interface TaskCardListProps {
  tasks: Task[];
}
export function TaskCardList({ tasks }: TaskCardListProps) {
  if (!tasks.length) {
    return (
      <div className="text-center text-text-secondary py-8">
        Задачи не найдены
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {tasks.map((task) => (
        <TaskCard key={task.taskCode} task={task} />
      ))}
    </div>
  );
}