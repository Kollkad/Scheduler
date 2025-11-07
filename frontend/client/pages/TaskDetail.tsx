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
    taskType: string;
    caseCode: string;
    responsibleExecutor: string;
    caseStage: string;
    taskText: string;
    reasonText?: string;
    monitoringStatus: string;
    isCompleted: boolean;
    failedChecksCount: number;
    sourceType: string;
    createdDate: string;
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
        
        if (taskData.sourceType === "documents") {
            console.log('⚠️ TODO: Нужно document_type и department для документа');
            navigate(`/case/${taskData.caseCode}`);
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
                    <span className="ml-2 text-gray-600">Загрузка данных задачи...</span>
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
                    <h2 className="text-xl font-semibold text-gray-900 mb-2">Ошибка загрузки</h2>
                    <p className="text-gray-600 mb-4">{error || 'Данные задачи не найдены'}</p>
                    <button
                        onClick={() => navigate(-1)}
                        className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-full hover:bg-gray-50"
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
                        taskData.isCompleted ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                        {taskData.isCompleted ? (
                            <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                        ) : (
                            <XCircle className="h-5 w-5 text-red-500 mr-2" />
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
                <h1 className="text-2xl font-bold text-gray-900">
                    Задача: {taskData.taskCode}
                </h1>
                <p className="text-gray-600 mt-1">{taskData.taskText}</p>
            </div>

            {/* Основная информация о задаче */}
            <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Левая колонка - основная информация */}
                    <div className="space-y-4">
                        <div>
                            <h3 className="text-sm font-medium text-gray-500">Код дела</h3>
                            <p className="mt-1 text-sm text-gray-900">{taskData.caseCode}</p>
                        </div>
                        
                        <div>
                            <h3 className="text-sm font-medium text-gray-500">Тип задачи</h3>
                            <p className="mt-1 text-sm text-gray-900">{taskData.taskType}</p>
                        </div>
                        
                        <div>
                            <h3 className="text-sm font-medium text-gray-500">Этап дела</h3>
                            <p className="mt-1 text-sm text-gray-900">{taskData.caseStage}</p>
                        </div>
                        
                        <div>
                            <h3 className="text-sm font-medium text-gray-500">Источник данных</h3>
                            <p className="mt-1 text-sm text-gray-900 capitalize">{taskData.sourceType}</p>
                        </div>
                    </div>

                    {/* Правая колонка - статусы и исполнитель */}
                    <div className="space-y-4">
                        <div>
                            <h3 className="text-sm font-medium text-gray-500">Ответственный исполнитель</h3>
                            <p className="mt-1 text-sm text-gray-900">{taskData.responsibleExecutor}</p>
                        </div>
                        
                        <div>
                            <h3 className="text-sm font-medium text-gray-500">Статус мониторинга</h3>
                            <p className="mt-1 text-sm text-gray-900">{taskData.monitoringStatus}</p>
                        </div>
                        
                        <div>
                            <h3 className="text-sm font-medium text-gray-500">Количество проваленных проверок</h3>
                            <p className="mt-1 text-sm text-gray-900">{taskData.failedChecksCount || 0}</p>
                        </div>
                        
                        <div>
                            <h3 className="text-sm font-medium text-gray-500">Дата создания</h3>
                            <p className="mt-1 text-sm text-gray-900">
                                {new Date(taskData.createdDate).toLocaleDateString('ru-RU')}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Причины постановки задачи */}
                <div className="pt-6 border-t border-gray-200">
                    <h3 className="text-sm font-medium text-gray-500 mb-2">Причины постановки задачи</h3>
                    <p className="text-sm text-gray-700">
                        {taskData.reasonText || "Причина не указана"}
                    </p>
                </div>
            </div>
        </PageContainer>
    );
}