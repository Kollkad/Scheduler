// frontend/client/pages/UserProfileDetail.tsx

import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Loader, RefreshCw, Copy } from "lucide-react";
import { PageContainer } from "@/components/PageContainer";
import { TabsContainer } from "@/components/TabsContainer";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/services/api/client";
import { API_ENDPOINTS } from "@/services/api/endpoints";
import { ProfileTasksTab } from "@/components/profile/ProfileTasksTab";
import { ProfileCasesTab } from "@/components/profile/ProfileCasesTab";
import { ProfileDocumentsTab } from "@/components/profile/ProfileDocumentsTab";
import { ProfileReportsTab } from "@/components/profile/ProfileReportsTab";
import { ProfileAnonymizationTab } from "@/components/profile/ProfileAnonymizationTab";
import { ProfileAdministrationTab } from "@/components/profile/ProfileAdministrationTab";
import { profileTabs, isTabVisible } from "@/components/profile/profileConfig";

interface UserInfo {
  login: string;
  email: string;
  name: string;
  role: string;
}

export function UserProfileDetail() {
  const navigate = useNavigate();
  const { tabId } = useParams<{ tabId?: string }>();
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [reloginLoading, setReloginLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const loadUser = () => {
    setLoading(true);
    apiClient.get<UserInfo>(API_ENDPOINTS.USER_INFO)
      .then(data => {
        setUser(data);
        setLoading(false);
      })
      .catch(() => {
        setUser(null);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadUser();
  }, []);

  const handleRelogin = async () => {
    setReloginLoading(true);
    try {
      await apiClient.post(API_ENDPOINTS.AUTH_LOGOUT);
      await apiClient.post(API_ENDPOINTS.AUTH_LOGIN);
      const data = await apiClient.get<UserInfo>(API_ENDPOINTS.USER_INFO);
      setUser(data);
    } catch {
      setUser(null);
    } finally {
      setReloginLoading(false);
    }
  };

  const handleCopyEmail = async () => {
    if (user?.email) {
      await navigator.clipboard.writeText(user.email);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const isGuest = user?.role === "Гость" || (!user && !loading);
  const retryButtonVariant = isGuest ? "warning" : "grayOutline";

  if (loading) {
    return (
      <PageContainer>
        <div className="flex items-center justify-center h-64">
          <Loader className="h-8 w-8 animate-spin text-blue" />
        </div>
      </PageContainer>
    );
  }

  // Формируем вкладки без контента — только id и label
  const visibleTabs = user
    ? profileTabs
        .filter(tab => isTabVisible(tab, user.role))
        .map(tab => ({ id: tab.id, label: tab.label }))
    : [];

  // Определяем активную вкладку из URL или первую доступную
  const activeTabId = tabId && visibleTabs.some(t => t.id === tabId)
    ? tabId
    : visibleTabs[0]?.id || "";

  // Контент только для активной вкладки
  const activeContent = (() => {
    if (!user) return null;
    switch (activeTabId) {
      case "tasks":
        return <ProfileTasksTab userName={user.name} />;
      case "cases":
        return <ProfileCasesTab userName={user.name || ""} />;
      case "documents":
        return <ProfileDocumentsTab />;
      case "reports":
        return <ProfileReportsTab />;
      case "anonymization":
        return <ProfileAnonymizationTab />;
      case "administration":
        return <ProfileAdministrationTab />;
      default:
        return null;
    }
  })();

  // Обработчик смены вкладки — меняет URL
  const handleTabChange = (newTabId: string) => {
    navigate(`/profile/${newTabId}`, { replace: true });
  };

  return (
    <PageContainer>
      {/* Верхняя панель */}
      <div className="mb-6 flex items-center justify-between">
        <Button
          variant="grayOutline"
          size="rounded"
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Вернуться назад
        </Button>

        <Button
          variant={retryButtonVariant as "warning" | "grayOutline"}
          size="rounded"
          onClick={handleRelogin}
          disabled={reloginLoading}
          className="inline-flex items-center gap-2"
        >
          {reloginLoading ? (
            <Loader className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          {reloginLoading ? "Вход..." : "Попробовать войти снова"}
        </Button>
      </div>

      {/* Информация о пользователе */}
      <div className="mb-6">
        {user ? (
          <>
            <h1 className="text-2xl font-bold text-text-primary">
              {user.role}: {user.name}
            </h1>
            <div className="flex items-center gap-2 mt-1">
              <p className="text-sm text-text-secondary">{user.email}</p>
              <button
                onClick={handleCopyEmail}
                className="p-1 hover:bg-bg-light-grey rounded transition-colors"
                title="Скопировать почту"
              >
                <Copy className="h-3.5 w-3.5 text-text-tertiary" />
              </button>
              {copied && (
                <span className="text-xs text-green">Скопировано</span>
              )}
            </div>
          </>
        ) : (
          <>
            <h1 className="text-2xl font-bold text-text-primary">Гость</h1>
            <p className="text-sm text-text-secondary mt-1">
              Не удалось загрузить пользователя. Попробуйте перезагрузить приложение или нажмите «Попробовать войти снова». Если ошибка повторится, попросите администратора проверить файл пользователей.
            </p>
          </>
        )}
      </div>

      {/* Вкладки */}
      {visibleTabs.length > 0 ? (
        <TabsContainer
          tabs={visibleTabs.map(tab => ({ ...tab, content: null }))}
          defaultTab={activeTabId}
          activeTab={activeTabId}
          onTabChange={handleTabChange}
        />
      ) : (
        <div className="text-center text-text-secondary py-8">
          {user ? "Нет доступных разделов" : "Вкладки появятся после входа"}
        </div>
      )}

      {/* Контент активной вкладки */}
      {activeContent && (
        <div className="mt-6">
          {activeContent}
        </div>
      )}
    </PageContainer>
  );
}

export default UserProfileDetail;
