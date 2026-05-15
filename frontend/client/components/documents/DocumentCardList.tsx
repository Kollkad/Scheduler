// frontend/client/components/documents/DocumentCardList.tsx

import { DocumentCard } from "@/components/documents/DocumentCard";

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

interface DocumentCardListProps {
  documents: DocumentItem[];
}

export function DocumentCardList({ documents }: DocumentCardListProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {documents.map(doc => (
        <DocumentCard key={doc.transferCode} document={doc} />
      ))}
    </div>
  );
}