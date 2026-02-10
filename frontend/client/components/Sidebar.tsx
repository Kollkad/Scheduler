// Sidebar.tsx
import { Link, useLocation } from "react-router-dom";
import { Rainbow, AlertCircle, FileText, Home, ClipboardList, Shield } from "lucide-react";
import { cn } from "@/utils/cn";
import { useEffect } from "react";
import { featureFlags } from '@/config/featureFlags';
import { useAnalysis } from "@/contexts/AnalysisContext";

const navigationItems = [
  { id: "overview", label: "Обзор системы", icon: Home, path: "/overview" },
  { id: "rainbow", label: "Rainbow", icon: Rainbow, path: "/rainbow" },
  { id: "terms", label: "Сроки сопровождения", icon: AlertCircle, path: "/terms" },
  { id: "tasks", label: "Задачи сотрудников", icon: ClipboardList, path: "/tasks" },
  { id: "depersonalization", label: "Обезличивание", icon: Shield, path: "/depersonalization" },
];

export function Sidebar() {
  const location = useLocation();
  const { uploadedFiles, refreshFilesStatus } = useAnalysis();

  // Загрузка статуса файлов при монтировании компонента
  useEffect(() => {
    refreshFilesStatus();
  }, [refreshFilesStatus]);

  // Формирование списка файлов для отображения
  const filesList = [
    {
      type: 'Текущий отчет',
      entry: uploadedFiles?.current_detailed_report
    },
    {
      type: 'Отчет по документам',
      entry: uploadedFiles?.documents_report
    },
    ...(featureFlags.enableComparison ? [{
      type: 'Предыдущий отчет',
      entry: uploadedFiles?.previous_detailed_report
    }] : [])
  ];

  return (
    <div className="w-80 h-screen fixed left-0 top-0 p-4">
      <div className="h-full rounded-3xl border flex flex-col" style={{ backgroundColor: 'rgba(28, 197, 60, 0.2)', borderColor: '#158F2C' }}>
        {/* Логотип */}
        <div className="p-6 border-b" style={{ borderColor: 'rgba(21, 143, 44, 0.3)' }}>
          <div className="flex items-center space-x-3">
            <img src="/logo-icon.png" alt="Логотип" className="w-8 h-8 object-contain" />
            <span className="text-xl font-semibold" style={{ color: '#1CC53C' }}>Планировщик</span>
          </div>
        </div>

        {/* Навигация */}
        <div className="flex-1 p-4">
          <nav className="space-y-2">
            {navigationItems.map((item) => {
              const isActive = location.pathname === item.path || (item.path === "/overview" && location.pathname === "/");
              const Icon = item.icon;
              return (
                <Link key={item.id} to={item.path} className={cn("flex items-center px-4 py-3 text-sm font-medium transition-colors rounded-2xl", isActive ? "text-white" : "hover:bg-white/20")} style={{ backgroundColor: isActive ? 'rgba(28, 197, 60, 0.3)' : 'transparent', color: isActive ? 'white' : '#1F1F1F' }}>
                  <Icon className="mr-3 h-5 w-5" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Загруженные файлы */}
        <div className="border-t p-4" style={{ borderColor: 'rgba(21, 143, 44, 0.3)' }}>
          <div className="flex items-center mb-2">
            <FileText className="h-4 w-4 mr-2" style={{ color: '#1CC53C' }} />
            <span className="text-sm font-medium" style={{ color: '#1F1F1F' }}>Загруженные файлы:</span>
          </div>

          <div className="space-y-2">
            {filesList.map((f, idx) => {
              const filename = f.entry?.filepath ? String(f.entry.filepath).split('/').pop() : 'Не загружен';
              const loaded = !!f.entry?.loaded;
              return (
                <div key={idx} className={cn("text-xs p-2 rounded-lg", loaded ? "bg-green-100" : "bg-gray-100")}>
                  <div className="font-medium" style={{ color: '#1F1F1F' }}>{f.type}:</div>
                  <div className={cn("truncate", loaded ? "text-green-700" : "text-gray-500")} title={filename}>
                    {loaded ? <span className="flex items-center"><span className="w-2 h-2 bg-green-500 rounded-full mr-1" />{filename}</span> : <span className="text-gray-400">{filename}</span>}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Статус готовности */}
          <div className="mt-3 p-2 bg-blue-50 rounded-lg">
            <div className="text-xs font-medium text-blue-800">
              Статус: {(uploadedFiles && ((uploadedFiles.current_detailed_report?.loaded ? 1 : 0) + (uploadedFiles.documents_report?.loaded ? 1 : 0)) >= 2) ?
                <span className="text-green-600">Готов к расчету</span> :
                <span className="text-orange-600">Ожидание файлов</span>
              }
            </div>
            <div className="text-xs text-blue-600">
              Загружено: { (uploadedFiles ? ((uploadedFiles.current_detailed_report?.loaded ? 1 : 0) + (uploadedFiles.documents_report?.loaded ? 1 : 0)) : 0) } из 2 обязательных
              {featureFlags.enableComparison && featureFlags.hasPreviousReport && " + предыдущий отчет"}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}