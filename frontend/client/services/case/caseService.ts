// client/services/case/caseService.ts

import { apiClient } from '@/services/api/client';
import { API_ENDPOINTS } from '@/services/api/endpoints';

export interface CaseField {
  id: string;
  label: string;
  value: any;
  type: 'text' | 'number' | 'date' | 'boolean' | 'currency';
  isEmpty?: boolean;
}

export interface CaseDetails {
  success: boolean;
  caseCode: string;
  data: Record<string, any>;
  fieldGroups: {
    general: CaseField[];
    dates: CaseField[];
    financial: CaseField[];
    court: CaseField[];
    other: CaseField[];
  };
  totalFields: number;
  foundInColumn?: string;
  caseStage?: string;
  rainbowColor?: string | null;
}

export interface DocumentDetails {
  success: boolean;
  transferCode: string;
  caseCode: string;
  documentType: string;
  department: string;
  fieldGroups: {
    general: CaseField[];
    dates: CaseField[];
    financial: CaseField[];
    court: CaseField[];
    other: CaseField[];
  };
  totalFields: number;
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

  // Метод получает детальную информацию о документе по коду передачи
  static async getDocumentDetails(transferCode: string): Promise<DocumentDetails> {
    try {
      const response = await apiClient.get<DocumentDetails>(
        `${API_ENDPOINTS.DOCUMENT_DETAILS}?transferCode=${encodeURIComponent(transferCode)}`
      );
      return response;
    } catch (error) {
      console.error('Error fetching document details:', error);
      throw error;
    }
  }
}