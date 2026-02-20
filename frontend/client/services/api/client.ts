// client\services\api\client.ts
import { 
  FilesStatusResponse, 
  StatusResponse, 
  UploadResponse,
  RemoveResponse 
} from './types';
import { API_ENDPOINTS } from './endpoints';

export class ApiClient {
  private static instance: ApiClient;

  static getInstance(): ApiClient {
    if (!ApiClient.instance) {
      ApiClient.instance = new ApiClient();
    }
    return ApiClient.instance;
  }

  // Метод выполняет GET запрос к указанному endpoint с опциональными параметрами
  async get<T>(endpoint: string, options?: { params?: Record<string, string> }): Promise<T> {
    let url = endpoint;
    // Добавление параметров запроса к URL если они предоставлены
    if (options?.params) {
      const params = new URLSearchParams();
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value);
        }
      });
      url += `?${params.toString()}`;
    }
    
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  }

  // Метод выполняет POST запрос к указанному endpoint с опциональным телом запроса
  async post<T>(endpoint: string, body?: any): Promise<T> {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  }

  // Метод для загрузки файлов (FormData)
  async uploadFile(endpoint: string, formData: FormData): Promise<UploadResponse> {
    const response = await fetch(endpoint, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Ошибка загрузки: ${response.statusText}`);
    }
    
    return await response.json();
  }

  // Метод для файлов (скачивание)
  async downloadFile(endpoint: string, params?: Record<string, string>): Promise<Blob> {
    let url = endpoint;
    
    if (params) {
      const searchParams = new URLSearchParams(params);
      url += `?${searchParams.toString()}`;
    }
    
    const response = await fetch(url, {
      headers: { 'Accept': 'application/octet-stream' },
      credentials: 'include'
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Download failed: ${response.status} - ${errorText}`);
    }
    
    return await response.blob();
  }

  // Удаление
  async delete<T>(endpoint: string): Promise<T> {
    const response = await fetch(endpoint, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  }

  // ==================== СПЕЦИАЛИЗИРОВАННЫЕ МЕТОДЫ ====================

  async getFilesStatus(): Promise<FilesStatusResponse> {
    return this.get<FilesStatusResponse>(API_ENDPOINTS.FILES_STATUS);
  }

  async getAllProcessedDataStatus(): Promise<StatusResponse> {
    return this.get<StatusResponse>(API_ENDPOINTS.SAVE_ALL_PROCESSED_DATA_STATUS);
  }

  async removeFile(fileType: string): Promise<RemoveResponse> {
    return this.delete<RemoveResponse>(`${API_ENDPOINTS.REMOVE_FILE}?file_type=${fileType}`);
  }
}

export const apiClient = ApiClient.getInstance();