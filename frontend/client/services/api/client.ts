// services/api/client.ts
const API_BASE_URL = 'http://localhost:8000';

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
    let url = `${API_BASE_URL}${endpoint}`;
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
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
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

  // Метод для файлов
  async downloadFile(endpoint: string, params?: Record<string, string>): Promise<Blob> {
    let url = `${API_BASE_URL}${endpoint}`;
    
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
}

export const apiClient = ApiClient.getInstance();