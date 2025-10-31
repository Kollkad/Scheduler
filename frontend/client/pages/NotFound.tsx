// src/pages/NotFound.tsx
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto text-center">
        <h1 className="text-2xl font-semibold text-gray-900 mb-4">Страница не найдена</h1>
        <p className="text-gray-600 mb-6">
          Запрашиваемая страница не существует.
        </p>
        <Button asChild>
          <Link to="/">Вернуться на главную</Link>
        </Button>
      </div>
    </div>
  );
}