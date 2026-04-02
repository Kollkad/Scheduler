// Sidebar.tsx
import { Link, useLocation } from "react-router-dom";
import { Rainbow, AlertCircle, FileText, Home, ClipboardList, Shield } from "lucide-react";
import { cn } from "@/utils/cn";
import { useEffect } from "react";
import { featureFlags } from '@/config/featureFlags';
import { useAnalysis } from "@/contexts/AnalysisContext";
import { formatDate } from "@/utils/dateFormat";

const navigationItems = [
  { id: "overview", label: "Обзор системы", icon: Home, path: "/overview" },
  { id: "rainbow", label: "Rainbow", icon: Rainbow, path: "/rainbow" },
  { id: "terms", label: "Сроки сопровождения", icon: AlertCircle, path: "/terms" },
  { id: "tasks", label: "Задачи сотрудников", icon: ClipboardList, path: "/tasks" },
  { id: "anonymization", label: "Обезличивание", icon: Shield, path: "/anonymization" },
];

export function Sidebar() {
  const location = useLocation();
  const { uploadedFiles, refreshFilesStatus } = useAnalysis();

  useEffect(() => {
    refreshFilesStatus();
  }, [refreshFilesStatus]);

  const getFileDate = (fileType: string): string => {
    const file = uploadedFiles?.files?.[fileType];
    if (!file?.loaded || !file.file?.uploaded_at) return '—';
    return formatDate(file.file.uploaded_at);
  };

  const isFileLoaded = (fileType: string): boolean => {
    return uploadedFiles?.files?.[fileType]?.loaded === true;
  };

  const loadedCount = [
    'current_detailed_report',
    'documents_report'
  ].filter(type => isFileLoaded(type)).length;

  const isReady = loadedCount === 2;

  return (
    <div className="w-80 h-screen fixed left-0 top-0 p-4">
      <div className="h-full rounded-3xl border border-green-dark flex flex-col bg-bg-green-transparent">
        {/* Логотип */}
        <div className="p-6 border-b border-green-semi-dark">
          <div className="flex items-center space-x-3">
            <img src="/logo-icon.png" alt="Логотип" className="w-8 h-8 object-contain" />
            <span className="text-xl font-semibold text-green">Планировщик</span>
          </div>
        </div>

        {/* Навигация */}
        <div className="flex-1 p-4">
          <nav className="space-y-2">
            {navigationItems.map((item) => {
              const isActive = location.pathname === item.path || (item.path === "/overview" && location.pathname === "/");
              const Icon = item.icon;
              return (
                <Link
                  key={item.id}
                  to={item.path}
                  className={cn(
                    "flex items-center px-4 py-3 text-sm font-medium transition-colors rounded-2xl",
                    isActive ? "bg-bg-green-transparent text-white" : "text-text-primary hover:bg-bg-green-transparent"
                  )}
                >
                  <Icon className="mr-3 h-5 w-5" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Загруженные файлы */}
        <div className="border-t border-green-semi-dark p-4">
          <div className="flex items-center mb-3">
            <FileText className="h-4 w-4 mr-2 text-green" />
            <span className="text-sm font-medium text-text-primary">Загруженные файлы:</span>
          </div>

          <div className={cn(
            "p-3 rounded-lg",
            isReady ? "bg-bg-light-green" : "bg-bg-ultra-light-grey"
          )}>
            <div className="text-sm space-y-1">
              <div>
                <span className="text-text-primary">Детальный отчет:</span>{' '}
                <span className={isFileLoaded('current_detailed_report') ? "text-green-dark" : "text-text-secondary"}>
                  {isFileLoaded('current_detailed_report') 
                    ? getFileDate('current_detailed_report')
                    : 'не загружен'}
                </span>
              </div>
              <div>
                <span className="text-text-primary">Отчет по документам:</span>{' '}
                <span className={isFileLoaded('documents_report') ? "text-green-dark" : "text-text-secondary"}>
                  {isFileLoaded('documents_report')
                    ? getFileDate('documents_report')
                    : 'не загружен'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}