// client/components/profile/ProfileReportsTab.tsx

import { useState, useEffect } from "react";
import { Loader, Download, Trash2 } from "lucide-react";
import { apiClient } from "@/services/api/client";
import { API_ENDPOINTS } from "@/services/api/endpoints";
import { Button } from "@/components/ui/button";

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

  // Скачать репорт
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

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Loader className="h-6 w-6 animate-spin text-blue" />
      </div>
    );
  }

  return (
    <div>
      <p className="text-sm text-text-secondary mb-4">Всего репортов: {reports.length}</p>

      {reports.length === 0 ? (
        <div className="text-center text-text-secondary py-8">
          Нет сохранённых репортов
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {reports.map(report => (
            <div key={report.id} className="bg-white rounded-lg border border-border p-4">
              <h4 className="font-medium text-text-primary mb-1">{report.name}</h4>
              <p className="text-xs text-text-secondary mb-3">{report.created_at}</p>

              <div className="flex gap-2">
                <Button
                  variant="grayOutline"
                  size="rounded"
                  onClick={() => handleDownload(report.id)}
                  className="inline-flex items-center gap-1"
                >
                  <Download className="h-4 w-4" />
                  Скачать
                </Button>
                <Button
                  variant="grayOutline"
                  size="rounded"
                  onClick={() => handleDelete(report.id)}
                  className="inline-flex items-center gap-1"
                >
                  <Trash2 className="h-4 w-4" />
                  Удалить
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
