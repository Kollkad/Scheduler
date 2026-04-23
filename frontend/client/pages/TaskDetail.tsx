// frontend/client/pages/TaskDetail.tsx

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Loader, Check, X, AlertCircle, Eraser} from "lucide-react";
import { PageContainer } from "@/components/PageContainer";
import { FieldGroup } from "@/components/FieldGroup";
import { TaskEditModal } from "@/components/TaskEditModal";
import { apiClient } from "@/services/api/client";
import { API_ENDPOINTS } from "@/services/api/endpoints";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/utils/dateFormat";
import { caseStageMapping } from "@/config/tableConfig";
import { CaseField } from "@/services/case/caseService";
import { Task } from "@/services/api/taskTypes";

export default function TaskDetail() {
    const navigate = useNavigate();
    const { taskCode } = useParams<{ taskCode: string }>();
    const [taskData, setTaskData] = useState<Task | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);

    // Загрузка данных задачи при изменении taskCode
    useEffect(() => {
        if (taskCode) {
            loadTaskData(taskCode);
        }
    }, [taskCode]);

    // Загружает детальную информацию о задаче по коду
    const loadTaskData = async (code: string) => {
        try {
            setLoading(true);
            const response = await apiClient.get<{ 
                success: boolean; 
                task: Task; 
                message?: string 
            }>(`${API_ENDPOINTS.TASK_DETAILS}/${code}`);
            
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

    // Переход к делу или документу, связанному с задачей
    const handleGoToSource = () => {
        if (!taskData) return;
        
        if (taskData.sourceType === "documents" && taskData.documentType && taskData.department) {
            navigate(`/document?caseCode=${encodeURIComponent(taskData.caseCode)}&documentType=${encodeURIComponent(taskData.documentType)}&department=${encodeURIComponent(taskData.department)}`);
        } else {
            navigate(`/case/${taskData.caseCode}`);
        }
    };

    // Обновляет данные задачи после успешного редактирования
    const handleEditSuccess = () => {
        if (taskCode) {
            loadTaskData(taskCode);
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

    // Формирует список полей для компонента FieldGroup
    const buildTaskFields = (): CaseField[] => {
        const fields: CaseField[] = [
            { id: 'caseCode', label: 'Код дела', value: taskData.caseCode, type: 'text' },
            { id: 'failedCheck', label: 'Название проверки', value: taskData.failedCheck, type: 'text' },
            { id: 'stageCode', label: 'Этап дела', value: caseStageMapping[taskData.stageCode] || taskData.stageCode, type: 'text' },
            { id: 'sourceType', label: 'Источник данных', value: taskData.sourceType === 'detailed' ? 'Детальный отчет' : taskData.sourceType, type: 'text' },
            { id: 'responsibleExecutor', label: 'Ответственный исполнитель', value: taskData.responsibleExecutor, type: 'text' },
            { id: 'monitoringStatus', label: 'Статус мониторинга', value: taskData.monitoringStatus, type: 'text' },
            { id: 'createdDate', label: 'Дата создания', value: formatDate(taskData.createdDate), type: 'text' },
        ];

        // Плановая дата включается только если задача не имеет переноса срока
        if (!taskData.hasOverride || !taskData.originalPlannedDate) {
            fields.push({ 
                id: 'executionDatePlan', 
                label: 'Плановая дата исполнения', 
                value: formatDate(taskData.executionDatePlan), 
                type: 'text' 
            });
        }

        return fields;
    };

    const hasShiftInfo = taskData.hasOverride && taskData.originalPlannedDate;

    // Удаляет пользовательское переопределение для задачи
    const handleClearOverride = async () => {
        if (!taskData) return;
        
        try {
            await apiClient.delete(`${API_ENDPOINTS.TASK_DELETE_OVERRIDE}/${taskData.taskCode}/override`);
            if (taskCode) {
                loadTaskData(taskCode);
            }
        } catch (error) {
            console.error('Ошибка удаления переопределения:', error);
            alert('Не удалось очистить изменения');
        }
    };

    return (
        <PageContainer>
            {/* Блок 1: Навигация и действия */}
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
                    <Button 
                        variant="grayOutline"
                        size="rounded"
                        onClick={() => setIsEditModalOpen(true)}
                    >
                        Изменить задачу
                    </Button>
                    
                    <Button 
                        variant="grayOutline"
                        size="rounded"
                        onClick={handleGoToSource}
                    >
                        {taskData.sourceType === "documents" ? "Перейти к документу" : "Перейти к делу"}
                    </Button>
                </div>
            </div>

            {/* Блок 2: Заголовок задачи с индикатором статуса */}
            <div className="mb-8">
                <div className="flex items-center gap-3 mb-2">
                    {/* Индикатор статуса выполнения с подсказкой при наведении */}
                    <div 
                        className={`flex items-center justify-center w-8 h-8 rounded-full ${
                            taskData.isCompleted ? 'bg-bg-light-green' : 'bg-red-light-transparent'
                        }`}
                        title={taskData.isCompleted ? "Задача считается выполненной" : "Задача считается не выполненной"}
                    >
                        {taskData.isCompleted ? (
                            <Check className="h-5 w-5 text-green" />
                        ) : (
                            <X className="h-5 w-5 text-red" />
                        )}
                    </div>
                    <h1 className="text-2xl font-bold text-text-primary">
                        Задача: {taskData.taskCode}
                    </h1>
                </div>
                {/* Текст и причины постановки задачи */}
                <p className="text-text-primary mt-1">Текст задачи: {taskData.taskText}</p>
                <p className="text-text-primary mt-1">Причины постановки задачи: {taskData.reasonText || "Причина не указана"}</p>
            </div>

            {/* Блок 3: Данные задачи */}
            <div className="space-y-6">
                <h2 className="text-lg font-semibold text-text-primary">Данные задачи</h2>
                <FieldGroup fields={buildTaskFields()} columns={2} showAlertIcon={false} />

                {/* Блок 4: Изменения срока (отображается только при наличии переноса) */}
                {hasShiftInfo && (
                    <div className="pt-6 border-t border-border">
                        <h2 className="text-lg font-semibold text-text-primary mb-4">Изменения срока</h2>
                        
                        <div className="space-y-2">
                            <p className="text-sm text-text-primary">
                                Причина изменения плановой даты исполнения: {taskData.shiftName || "—"}
                            </p>
                            <p className="text-sm text-text-primary">
                                Прежняя дата исполнения: {formatDate(taskData.originalPlannedDate) || "—"}
                            </p>
                            <p className="text-sm text-text-primary">
                                Новая дата исполнения: {formatDate(taskData.executionDatePlan) || "—"}
                            </p>
                        </div>
                        
                        {/* Кнопка очистки изменений */}
                        <div className="mt-4">
                            <Button 
                                variant="grayOutline"
                                size="rounded"
                                onClick={handleClearOverride}
                                className="inline-flex items-center gap-2"
                            >
                                <Eraser className="h-4 w-4" />
                                Очистить изменения
                            </Button>
                        </div>
                    </div>
                )}
            </div>

            {/* Модальное окно редактирования задачи */}
            <TaskEditModal
                isOpen={isEditModalOpen}
                onClose={() => setIsEditModalOpen(false)}
                task={taskData}
                onSuccess={handleEditSuccess}
            />
        </PageContainer>
    );
}
