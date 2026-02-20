//client\services\api\types.ts

// ==================== FILE OPERATIONS ====================
export interface FileStatus {
  loaded: boolean;
  filepath: string | null;
  exists: boolean;
}

export interface FilesStatusResponse {
  current_detailed_report: FileStatus;
  documents_report: FileStatus;
  previous_detailed_report: FileStatus;
  ready_for_analysis: boolean;
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

// ==================== UPLOAD ====================
export interface UploadResponse {
  message: string;
  filename: string;
  file_type: string;
  filepath: string;
}

// ==================== REMOVE ====================
export interface RemoveResponse {
  message: string;
  file_type: string;
  removed: boolean;
}


