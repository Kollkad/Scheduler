// frontend/client/pages/TaskDetail.tsx
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Loader, CheckCircle, XCircle, AlertCircle } from "lucide-react";
import { PageContainer } from "@/components/PageContainer";
import { apiClient } from "@/services/api/client";
import { API_ENDPOINTS } from "@/services/api/endpoints";
import { Button } from "@/components/ui/button";

type TaskDetails = {
    taskCode: string;
    failedCheck: string;
    caseCode: string;
    responsibleExecutor: string;
    caseStage: string;
    taskText: string;
    reasonText?: string;
    monitoringStatus: string;
    isCompleted: boolean;
    sourceType: string;
    createdDate: string;
    documentType?: string;
    department?: string;
    requestCode?: string;
};
export default function TaskDetail() {
    const navigate = useNavigate();
    const { taskCode } = useParams<{ taskCode: string }>();
    const [taskData, setTaskData] = useState<TaskDetails | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Загрузка данных задачи при изменении taskCode
    useEffect(() => {
        if (taskCode) {
            loadTaskData(taskCode);
        }
    }, [taskCode]);

    const loadTaskData = async (code: string) => {
        try {
            setLoading(true);
            console.log('🔄 Загрузка данных для задачи:', code);
            
            const response = await apiClient.get<{ 
                success: boolean; 
                task: TaskDetails; 
                message?: string 
            }>(`${API_ENDPOINTS.TASK_DETAILS}/${code}`);
            
            console.log('✅ Данные задачи получены:', response);
            
            if (response && response.success && response.task) {
                setTaskData(response.task);
            } else {
                throw new Error(response?.message || 'Данные задачи не найдены');
            }
        } catch (err) {
            console.error('❌ Ошибка загрузки:', err);
            setError(err instanceof Error ? err.message : 'Ошибка загрузки данных задачи');
            setTaskData(null);
        } finally {
            setLoading(false);
        }
    };

    // Обработка перехода к источнику задачи
    const handleGoToSource = () => {
        if (!taskData) return;
        
        if (taskData.sourceType === "documents" && taskData.documentType && taskData.department) {
            navigate(`/document?caseCode=${encodeURIComponent(taskData.caseCode)}&documentType=${encodeURIComponent(taskData.documentType)}&department=${encodeURIComponent(taskData.department)}`);
        } else {
            navigate(`/case/${taskData.caseCode}`);
        }
    };

    // Состояние загрузки
    if (loading) {
        return (
            <PageContainer>
                <div className="flex items-center justify-center h-64">
                    <Loader className="h-8 w-8 animate-spin text-blue-500" />
                    <span className="ml-2 text-text-secondary">Загрузка данных задачи...</span>
                </div>
            </PageContainer>
        );
    }

    // Состояние ошибки
    if (error || !taskData) {
        return (
            <PageContainer>
                <div className="text-center py-8">
                    <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
                    <h2 className="text-xl font-semibold text-text-primary mb-2">Ошибка загрузки</h2>
                    <p className="text-text-secondary mb-4">{error || 'Данные задачи не найдены'}</p>
                    <button
                        onClick={() => navigate(-1)}
                        className="inline-flex items-center px-4 py-2 text-sm font-medium text-text-secondary bg-white border border-gray-300 rounded-full hover:bg-gray-50"
                    >
                        <ArrowLeft className="h-4 w-4 mr-2" />
                        Вернуться назад
                    </button>
                </div>
            </PageContainer>
        );
    }

    return (
        <PageContainer>
            {/* Заголовок и навигация */}
            <div className="flex items-center justify-between mb-6">
                <Button 
                    variant="grayOutline"
                    size="rounded"
                    onClick={() => navigate(-1)}
                    className="inline-flex items-center gap-2"
                    >
                    <ArrowLeft className="h-4 w-4" />
                    Вернуться назад
                </Button>
                
                <div className="flex items-center gap-3">
                    {/* Статус выполнения задачи */}
                    <div className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-medium ${
                        taskData.isCompleted ? 'bg-bg-light-green text-green-dark' : 'bg-red-light-transparent text-dark-default'
                    }`}>
                        {taskData.isCompleted ? (
                            <CheckCircle className="h-5 w-5 text-green mr-2" />
                        ) : (
                            <XCircle className="h-5 w-5 text-red mr-2" />
                        )}
                        <span>{taskData.isCompleted ? "Выполнена" : "Не выполнена"}</span>
                    </div>
                    
                    {/* Кнопка перехода к источнику */}
                    <Button 
                        variant="grayOutline"
                        size="rounded"
                        onClick={handleGoToSource}
                        >
                        {taskData.sourceType === "documents" ? "Перейти к документу" : "Перейти к делу"}
                    </Button>
                </div>
            </div>

            {/* Заголовок задачи */}
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-text-primary">
                    Задача: {taskData.taskCode}
                </h1>
                <p className="text-text-secondary mt-1">{taskData.taskText}</p>
            </div>

            {/* Основная информация о задаче */}
            <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Левая колонка - основная информация */}
                    <div className="space-y-4">
                        <div>
                            <h3 className="text-sm font-medium text-text-primary">Код дела</h3>
                            <p className="mt-1 text-sm text-text-primary">{taskData.caseCode}</p>
                        </div>
                        
                        <div>
                            <h3 className="text-sm font-medium text-text-primary">Название проверки</h3>
                            <p className="mt-1 text-sm text-text-primary">{taskData.failedCheck}</p>
                        </div>
                        
                        <div>
                            <h3 className="text-sm font-medium text-text-primary">Этап дела</h3>
                            <p className="mt-1 text-sm text-text-primary">{taskData.caseStage}</p>
                        </div>
                        
                        <div>
                            <h3 className="text-sm font-medium text-text-primary">Источник данных</h3>
                            <p className="mt-1 text-sm text-text-primary capitalize">{taskData.sourceType}</p>
                        </div>
                    </div>

                    {/* Правая колонка - статусы и исполнитель */}
                    <div className="space-y-4">
                        <div>
                            <h3 className="text-sm font-medium text-text-primary">Ответственный исполнитель</h3>
                            <p className="mt-1 text-sm text-text-primary">{taskData.responsibleExecutor}</p>
                        </div>
                        
                        <div>
                            <h3 className="text-sm font-medium text-text-primary">Статус мониторинга</h3>
                            <p className="mt-1 text-sm text-text-primary">{taskData.monitoringStatus}</p>
                        </div>
                        
                        <div>
                            <h3 className="text-sm font-medium text-text-primary">Дата создания</h3>
                            <p className="mt-1 text-sm text-text-primary">
                                {new Date(taskData.createdDate).toLocaleDateString('ru-RU')}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Причины постановки задачи */}
                <div className="pt-6 border-t border-border-default">
                    <h3 className="text-sm font-medium text-text-primary mb-2">Причины постановки задачи</h3>
                    <p className="text-sm text-text-primary">
                        {taskData.reasonText || "Причина не указана"}
                    </p>
                </div>
            </div>
        </PageContainer>
    );
}