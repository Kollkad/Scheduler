// client/pages/UserProfileDetail.tsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Loader } from "lucide-react";
import { PageContainer } from "@/components/PageContainer";
import { Button } from "@/components/ui/button";
import { apiClient } from '@/services/api/client';
import { API_ENDPOINTS } from '@/services/api/endpoints';

interface UserInfo {
  login: string;
  email: string;
  name: string;
  role: string;
}

export function UserProfileDetail() {
  const navigate = useNavigate();
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.get<UserInfo>(API_ENDPOINTS.USER_INFO)
        .then(data => {
        setUser(data);
        setLoading(false);
        })
        .catch(() => setLoading(false));
    }, []);

  if (loading) {
    return (
      <PageContainer>
        <div className="flex items-center justify-center h-64">
          <Loader className="h-8 w-8 animate-spin" />
        </div>
      </PageContainer>
    );
  }

  if (!user) {
    return (
      <PageContainer>
        <div className="text-center text-red-600">
          Не удалось загрузить данные пользователя
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
        <div className="mb-6">
        <Button 
            variant="grayOutline"
            size="rounded"
            onClick={() => navigate(-1)}
            className="inline-flex items-center gap-2"
        >
            <ArrowLeft className="h-4 w-4" />
            Вернуться назад
        </Button>
        </div>

        <div>
        <h1 className="text-2xl font-bold text-text-primary">
            {user.role}: {user.name}
        </h1>
        <p className="text-sm text-text-secondary mt-1">
            {user.email}
        </p>
        </div>
    </PageContainer>
    );
}

export default UserProfileDetail;