// services/case/caseService.ts
import { apiClient } from '@/services/api/client';
import { API_ENDPOINTS } from '@/services/api/endpoints';

export interface CaseField {
  id: string;
  label: string;
  value: any;
  type: 'text' | 'number' | 'date' | 'boolean' | 'currency';
}

export interface CaseDetails {
  success: boolean;
  caseCode: string;
  data: Record<string, any>;
  fieldGroups: Record<string, CaseField[]>;
  totalFields: number;
  foundInColumn?: string;
}

export interface DocumentDetails {
  success: boolean;
  caseCode: string;
  documentType: string;
  department: string;
  document: Record<string, any>;
  message: string;
}

export class CaseService {
  // Метод получает детальную информацию о деле по коду
  static async getCaseDetails(caseCode: string): Promise<CaseDetails> {
    try {
      const response = await apiClient.get<CaseDetails>(
        `${API_ENDPOINTS.CASE_DETAILS}/${caseCode}`
      );
      return response;
    } catch (error) {
      console.error('Error fetching case details:', error);
      throw error;
    }
  }

  // Метод получает детальную информацию о документе по коду дела, типу документа и подразделению
  static async getDocumentDetails(
    caseCode: string, 
    documentType: string, 
    department: string
  ): Promise<DocumentDetails> {
    try {
      const response = await apiClient.get<DocumentDetails>(
        `${API_ENDPOINTS.DOCUMENT_DETAILS}?case_code=${encodeURIComponent(caseCode)}&document_type=${encodeURIComponent(documentType)}&department=${encodeURIComponent(department)}`
      );
      return response;
    } catch (error) {
      console.error('Error fetching document details:', error);
      throw error;
    }
  }
}