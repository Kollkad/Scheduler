// client/services/api/types.ts

// ==================== FILE OPERATIONS ====================
export interface FileModel {
  id: string;
  name: string;
  type: string;
  server_path: string;
  uploaded_at: string;
  uploaded_by: string;
}

export interface FileStatus {
  loaded: boolean;
  exists: boolean;
  file: FileModel | null;
}

export interface FilesStatusResponse {
  files: Record<string, FileStatus>;
  total_files: number;
}

export interface SingleFileStatusResponse {
  file_type: string;
  exists: boolean;
  file: FileModel | null;
}

// ==================== UPLOAD ====================
export interface UploadResponse {
  message: string;
  file: FileModel;
}

// ==================== REMOVE ====================
export interface RemoveResponse {
  message: string;
  file_type: string;
  removed: boolean;
}

// ==================== SAVING ====================
export interface DataSetStatus {
  loaded: boolean;
  row_count: number;
}

export interface AvailableDataStatus {
  detailed_report: DataSetStatus;
  documents_report: DataSetStatus;
  terms_productions: DataSetStatus;
  documents_analysis: DataSetStatus;
  tasks: DataSetStatus;
}

export interface StatusResponse {
  success: boolean;
  status: AvailableDataStatus;
  message: string;
}


