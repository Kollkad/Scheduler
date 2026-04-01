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
      <div className="h-full rounded-3xl border border-border-green flex flex-col bg-green-sidebar">
        {/* Логотип */}
        <div className="p-6 border-b" style={{ borderColor: 'rgba(21, 143, 44, 0.3)' }}>
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
                    isActive ? "bg-green-active text-white" : "text-text-inactive hover:bg-white/20"
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
        <div className="border-t p-4" style={{ borderColor: 'rgba(21, 143, 44, 0.3)' }}>
          <div className="flex items-center mb-3">
            <FileText className="h-4 w-4 mr-2 text-green" />
            <span className="text-sm font-medium text-text-inactive">Загруженные файлы:</span>
          </div>

          <div className={cn(
            "p-3 rounded-lg",
            isReady ? "bg-green-100" : "bg-gray-100"
          )}>
            <div className="text-sm space-y-1">
              <div>
                <span className="text-text-inactive">Детальный отчет:</span>{' '}
                <span className={isFileLoaded('current_detailed_report') ? "text-green-700" : "text-gray-500"}>
                  {isFileLoaded('current_detailed_report') 
                    ? formatDate(uploadedFiles?.files?.current_detailed_report?.file?.uploaded_at)
                    : 'не загружен'}
                </span>
              </div>
              <div>
                <span className="text-text-inactive">Отчет по документам:</span>{' '}
                <span className={isFileLoaded('documents_report') ? "text-green-700" : "text-gray-500"}>
                  {isFileLoaded('documents_report')
                    ? formatDate(uploadedFiles?.files?.documents_report?.file?.uploaded_at)
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