// client/components/profile/ProfileReportsTab.tsx

import { useState, useEffect, useMemo } from "react";
import { Loader, Download, Trash2 } from "lucide-react";
import { apiClient } from "@/services/api/client";
import { API_ENDPOINTS } from "@/services/api/endpoints";
import { SortButton } from "@/components/tables/SortButton";

interface ReportItem {
  id: string;
  type: string;
  name: string;
  filepath: string;
  folder: string;
  created_at: string;
}

export function ProfileReportsTab() {
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedNames, setSelectedNames] = useState<string[]>([]);

  // Загрузка списка репортов
  const loadReports = () => {
    setLoading(true);
    apiClient.get<{ success: boolean; reports: ReportItem[] }>(`${API_ENDPOINTS.REPORTS_LIST}`)
      .then(data => {
        if (data.success) setReports(data.reports);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadReports();
  }, []);

  // Все уникальные имена репортов
  const reportNameOptions = useMemo(() => {
    const names = new Set<string>();
    reports.forEach(r => names.add(r.name));
    return Array.from(names).sort();
  }, [reports]);

  // Фильтрация по выбранным именам
  const filteredReports = useMemo(() => {
    if (selectedNames.length === 0) return reports;
    return reports.filter(r => selectedNames.includes(r.name));
  }, [reports, selectedNames]);

  const handleDownload = (reportId: string) => {
    window.open(`${API_ENDPOINTS.REPORTS_LIST}/${reportId}/download`, "_blank");
  };

  // Удалить репорт
  const handleDelete = async (reportId: string) => {
    try {
      await apiClient.delete(`${API_ENDPOINTS.REPORTS_LIST}/${reportId}`);
      loadReports();
    } catch (error) {
      console.error("Ошибка удаления репорта:", error);
    }
  };

  const hasActiveFilter = selectedNames.length > 0;

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Loader className="h-6 w-6 animate-spin text-blue" />
      </div>
    );
  }

  return (
    <div>
      {/* Заголовок + фильтр */}
      <div className="flex items-center gap-2 mb-1">
        <h3 className="text-lg font-medium text-text-primary">Репорты</h3>
        <SortButton
          onSortChange={() => {}}
          onFilterChange={setSelectedNames}
          filterOptions={reportNameOptions.map(name => ({ value: name, label: name }))}
          selectedFilterValues={selectedNames}
          isActive={hasActiveFilter}
        />
      </div>

      {/* Количество репортов */}
      <p className="text-sm text-text-primary mb-4">
        Найдено репортов: {filteredReports.length}
        {hasActiveFilter && (
          <button 
            onClick={() => setSelectedNames([])}
            className="text-xs text-blue hover:underline ml-2"
          >
            Сбросить фильтр
          </button>
        )}
      </p>

      {filteredReports.length === 0 ? (
        <div className="text-center text-text-secondary py-8">
          Нет сохранённых репортов
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredReports.map(report => (
            <div key={report.id} className="bg-white rounded-lg border border-border p-4 relative">
              <div className="pr-16">
                <h4 className="font-medium text-text-primary mb-1">{report.name}</h4>
                <p className="text-xs text-text-secondary">{report.created_at}</p>
              </div>

              <div className="absolute top-3 right-3 flex gap-1">
                <button
                  onClick={() => handleDownload(report.id)}
                  className="p-1.5 hover:bg-bg-light-grey rounded transition-colors text-text-secondary hover:text-text-primary"
                  title="Скачать"
                >
                  <Download className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleDelete(report.id)}
                  className="p-1.5 hover:bg-red-light rounded transition-colors text-text-secondary hover:text-red"
                  title="Удалить"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
