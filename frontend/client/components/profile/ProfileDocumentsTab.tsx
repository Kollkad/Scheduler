// frontend/client/components/profile/ProfileDocumentsTab.tsx

import { useState, useEffect, useMemo } from "react";
import { Loader } from "lucide-react";
import { apiClient } from "@/services/api/client";
import { API_ENDPOINTS } from "@/services/api/endpoints";
import { DocumentCardList } from "@/components/documents/DocumentCardList";
import { SortButton } from "@/components/tables/SortButton";

interface DocumentTask {
  taskCode: string;
  taskText: string;
  isCompleted: boolean;
  docTransferCode: string;
}

interface DocumentItem {
  transferCode: string;
  caseCode: string;
  documentType: string;
  department: string;
  responsibleExecutor: string;
  tasks: DocumentTask[];
}

interface DocumentsResponse {
  success: boolean;
  documents: DocumentItem[];
  tasks: DocumentTask[];
  totalDocuments: number;
  message: string;
}

interface ProfileDocumentsTabProps {
  userName: string;
}

export function ProfileDocumentsTab({ userName }: ProfileDocumentsTabProps) {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTransferCodes, setSelectedTransferCodes] = useState<string[]>([]);

  useEffect(() => {
    if (!userName) return;

    setLoading(true);
    const url = `${API_ENDPOINTS.DOCUMENTS_WITH_TASKS}?executor=${encodeURIComponent(userName)}`;
    apiClient.get<DocumentsResponse>(url)
      .then(data => {
        if (data.success) {
          // Группируем задачи по transferCode
          const tasksByDoc = new Map<string, DocumentTask[]>();
          data.tasks.forEach(task => {
            const code = task.docTransferCode;
            if (!tasksByDoc.has(code)) tasksByDoc.set(code, []);
            tasksByDoc.get(code)!.push(task);
          });

          const enrichedDocs = data.documents.map(d => ({
            ...d,
            tasks: tasksByDoc.get(d.transferCode) || [],
          }));

          setDocuments(enrichedDocs);
        }
      })
      .catch(() => setDocuments([]))
      .finally(() => setLoading(false));
  }, [userName]);

  // Все коды передачи для фильтрации
  const transferCodeOptions = useMemo(() => {
    return documents.map(d => d.transferCode).sort();
  }, [documents]);

  // Фильтрация
  const filteredDocuments = useMemo(() => {
    if (selectedTransferCodes.length === 0) return documents;
    return documents.filter(d => selectedTransferCodes.includes(d.transferCode));
  }, [documents, selectedTransferCodes]);

  const hasActiveFilter = selectedTransferCodes.length > 0;

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
        <h3 className="text-lg font-medium text-text-primary">Документы</h3>
        <SortButton
          onSortChange={() => {}}
          onFilterChange={setSelectedTransferCodes}
          filterOptions={transferCodeOptions.map(code => ({ value: code, label: code }))}
          selectedFilterValues={selectedTransferCodes}
          isActive={hasActiveFilter}
        />
      </div>

      {/* Количество документов */}
      <p className="text-sm text-text-primary mb-4">
        Найдено документов: {filteredDocuments.length}
        {hasActiveFilter && (
          <button
            onClick={() => setSelectedTransferCodes([])}
            className="text-xs text-blue hover:underline ml-2"
          >
            Сбросить фильтр
          </button>
        )}
      </p>

      {/* Список документов */}
      {filteredDocuments.length > 0 ? (
        <DocumentCardList documents={filteredDocuments} />
      ) : (
        <div className="text-center text-text-secondary py-8">
          Нет документов
        </div>
      )}
    </div>
  );
}
