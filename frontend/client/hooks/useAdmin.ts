//client/hooks/useAdmin.ts
import { useState, useEffect } from 'react';
import { apiClient } from '@/services/api/client';
import { API_ENDPOINTS } from '@/services/api/endpoints';

interface AdminStatus {
  isAdmin: boolean;
  message: string;
}

export function useAdmin() {
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAdminStatus = async () => {
      try {
        const response = await apiClient.get<AdminStatus>(API_ENDPOINTS.ADMIN_STATUS);
        setIsAdmin(response.isAdmin);
      } catch (error) {
        console.error('Ошибка проверки прав администратора:', error);
        setIsAdmin(false);
      } finally {
        setLoading(false);
      }
    };

    checkAdminStatus();
  }, []);

  return { isAdmin, loading };
}