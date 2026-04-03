// frontend/client/components/TaskCardList.tsx

import { TaskCard } from "@/components/TaskCard";

interface Task {
  taskCode: string;
  taskText: string;
  reasonText?: string;
  isCompleted: boolean;
  executionDatePlan?: string;
  executionDateFact?: string;
}

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
        <TaskCard key={task.taskCode} {...task} />
      ))}
    </div>
  );
}