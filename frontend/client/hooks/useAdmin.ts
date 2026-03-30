// client/hooks/useAdmin.ts
import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/services/api/client';
import { API_ENDPOINTS } from '@/services/api/endpoints';

interface AuthStatus {
  authenticated: boolean;
  login: string | null;
  email: string | null;
  name: string | null;
  role: string | null;
}

export function useAdmin() {
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const { authChecked } = useAuth();

  useEffect(() => {
    if (!authChecked) return;

    const checkAdminStatus = async () => {
      try {
        const response = await apiClient.get<AuthStatus>(API_ENDPOINTS.AUTH_STATUS);
        setIsAdmin(response.role === 'Администратор');
      } catch (error) {
        console.error('Ошибка проверки прав администратора:', error);
        setIsAdmin(false);
      } finally {
        setLoading(false);
      }
    };

    checkAdminStatus();
  }, [authChecked]);

  return { isAdmin, loading };
}