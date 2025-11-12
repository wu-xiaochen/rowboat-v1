'use client';

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/common/panel-common";
import { fetchRecurringJobRule, toggleRecurringJobRule, deleteRecurringJobRule } from "@/app/actions/recurring-job-rules.actions";
import { ArrowLeftIcon, PlayIcon, PauseIcon, ClockIcon, AlertCircleIcon, Trash2Icon } from "lucide-react";
import Link from "next/link";
import { RecurringJobRule } from "@/src/entities/models/recurring-job-rule";
import { Spinner } from "@heroui/react";
import { z } from "zod";
import { JobsList } from "@/app/projects/[projectId]/jobs/components/jobs-list";

export function RecurringJobRuleView({ projectId, ruleId }: { projectId: string; ruleId: string }) {
    const router = useRouter();
    const [rule, setRule] = useState<z.infer<typeof RecurringJobRule> | null>(null);
    const [loading, setLoading] = useState(true);
    const [updating, setUpdating] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

    const jobsFilters = useMemo(() => ({ recurringJobRuleId: ruleId }), [ruleId]);

    useEffect(() => {
        const loadRule = async () => {
            try {
                const fetchedRule = await fetchRecurringJobRule({ ruleId });
                setRule(fetchedRule);
            } catch (error) {
                console.error("Failed to fetch rule:", error);
            } finally {
                setLoading(false);
            }
        };

        loadRule();
    }, [ruleId]);

    const handleToggleStatus = async () => {
        if (!rule) return;
        
        setUpdating(true);
        try {
            const updatedRule = await toggleRecurringJobRule({
                ruleId: rule.id,
                disabled: !rule.disabled,
            });
            setRule(updatedRule);
        } catch (error) {
            console.error("Failed to update rule:", error);
            alert("更新规则状态失败");
        } finally {
            setUpdating(false);
        }
    };

    const handleDelete = async () => {
        if (!rule) return;
        
        setDeleting(true);
        try {
            await deleteRecurringJobRule({
                projectId,
                ruleId: rule.id,
            });
            // Redirect back to job rules list
            router.push(`/projects/${projectId}/manage-triggers?tab=recurring`);
        } catch (error) {
            console.error("Failed to delete rule:", error);
            alert("删除规则失败");
        } finally {
            setDeleting(false);
            setShowDeleteConfirm(false);
        }
    };

    const formatCronExpression = (cron: string) => {
        // Simple cron formatting for display
        const parts = cron.split(' ');
        if (parts.length === 5) {
            const [minute, hour, day, month, dayOfWeek] = parts;
            if (minute === '*' && hour === '*' && day === '*' && month === '*' && dayOfWeek === '*') {
                return '每分钟';
            }
            if (minute === '0' && hour === '*' && day === '*' && month === '*' && dayOfWeek === '*') {
                return '每小时';
            }
            if (minute === '0' && hour === '0' && day === '*' && month === '*' && dayOfWeek === '*') {
                return '每天午夜';
            }
            if (minute === '0' && hour === '0' && day === '1' && month === '*' && dayOfWeek === '*') {
                return '每月1日';
            }
            if (minute === '0' && hour === '0' && day === '*' && month === '*' && dayOfWeek === '0') {
                return '每周日';
            }
        }
        return cron;
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString();
    };

    if (loading) {
        return (
            <Panel title="加载中...">
                <div className="flex items-center justify-center h-64">
                    <Spinner size="lg" />
                </div>
            </Panel>
        );
    }

    if (!rule) {
        return (
            <Panel title="未找到规则">
                <div className="text-center py-8">
                    <p className="text-gray-500 dark:text-gray-400">未找到请求的规则。</p>
                    <Link href={`/projects/${projectId}/manage-triggers`}>
                        <Button variant="secondary" className="mt-4">
                            返回任务规则
                        </Button>
                    </Link>
                </div>
            </Panel>
        );
    }

    return (
        <>
            <Panel
                title={
                    <div className="flex items-center gap-3">
                        <Link href={`/projects/${projectId}/manage-triggers?tab=recurring`}>
                            <Button variant="secondary" size="sm" startContent={<ArrowLeftIcon className="w-4 h-4" />} className="whitespace-nowrap">
                                返回
                            </Button>
                        </Link>
                        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                            重复任务规则
                        </div>
                    </div>
                }
                rightActions={
                    <div className="flex items-center gap-3">
                        <Button
                            onClick={handleToggleStatus}
                            disabled={updating}
                            variant={rule.disabled ? "primary" : "secondary"}
                            size="sm"
                            isLoading={updating}
                            startContent={rule.disabled ? <PlayIcon className="w-4 h-4" /> : <PauseIcon className="w-4 h-4" />}
                            className="whitespace-nowrap"
                        >
                            {rule.disabled ? '恢复' : '暂停'}
                        </Button>
                        <Button
                            onClick={() => setShowDeleteConfirm(true)}
                            variant="secondary"
                            size="sm"
                            startContent={<Trash2Icon className="w-4 h-4" />}
                            className="bg-red-50 hover:bg-red-100 text-red-700 dark:bg-red-950 dark:hover:bg-red-900 dark:text-red-400 border border-red-200 dark:border-red-800 whitespace-nowrap"
                        >
                            删除
                        </Button>
                    </div>
                }
            >
                <div className="h-full overflow-auto px-4 py-4">
                    <div className="max-w-[800px] mx-auto space-y-6">
                        {/* Status */}
                        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                            <div className="flex items-center gap-2 mb-2">
                                <div className={`w-3 h-3 rounded-full ${rule.disabled ? 'bg-red-500' : 'bg-green-500'}`} />
                                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                    状态：{rule.disabled ? '已禁用' : '激活'}
                                </span>
                            </div>
                            {rule.lastError && (
                                <div className="flex items-start gap-2 mt-2 p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded">
                                    <AlertCircleIcon className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                                    <div className="text-sm text-red-700 dark:text-red-300">
                                        <strong>上次错误：</strong> {rule.lastError}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Schedule Information */}
                        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-3">
                                计划信息
                            </h3>
                            <div className="space-y-3">
                                <div className="flex items-center gap-2">
                                    <ClockIcon className="w-4 h-4 text-gray-500" />
                                    <span className="text-sm text-gray-600 dark:text-gray-400">Cron表达式：</span>
                                    <code className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-sm font-mono">
                                        {rule.cron}
                                    </code>
                                </div>
                                <div className="text-sm text-gray-600 dark:text-gray-400">
                                    <strong>可读格式：</strong> {formatCronExpression(rule.cron)}
                                </div>
                                <div className="text-sm text-gray-600 dark:text-gray-400">
                                    <strong>下次运行：</strong> {formatDate(rule.nextRunAt)}
                                </div>
                                {rule.lastProcessedAt && (
                                    <div className="text-sm text-gray-600 dark:text-gray-400">
                                        <strong>上次运行：</strong> {formatDate(rule.lastProcessedAt)}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Messages */}
                        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-3">
                                规则输入
                            </h3>
                            <div className="space-y-3">
                                <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                                    消息 ({rule.input.messages.length})
                                </div>
                                {rule.input.messages.map((message, index) => (
                                    <div key={index} className="border border-gray-200 dark:border-gray-600 rounded-lg p-3">
                                        <div className="flex items-center gap-2 mb-2">
                                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                                                message.role === 'system' 
                                                    ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                                                    : message.role === 'user'
                                                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                                    : 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
                                            }`}>
                                                {message.role === 'system' ? '系统' : message.role === 'user' ? '用户' : '助手'}
                                            </span>
                                        </div>
                                        <div className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                                            {message.content}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Metadata */}
                        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-3">
                                元数据
                            </h3>
                            <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                                <div><strong>创建时间：</strong> {formatDate(rule.createdAt)}</div>
                                {rule.updatedAt && (
                                    <div><strong>更新时间：</strong> {formatDate(rule.updatedAt)}</div>
                                )}
                                <div><strong>规则ID：</strong> <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">{rule.id}</code></div>
                            </div>
                        </div>

                        {/* Jobs Created by This Rule */}
                        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-3">
                                最近任务
                            </h3>
                            <JobsList 
                                projectId={projectId} 
                                filters={jobsFilters}
                                showTitle={false}
                            />
                        </div>
                    </div>
                </div>
            </Panel>

            {/* Delete Confirmation Modal */}
            {showDeleteConfirm && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md mx-4">
                        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
                            确认删除规则
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                            确定要删除此重复任务规则吗？此操作无法撤销，将永久删除该规则及其所有相关数据。
                        </p>
                        <div className="flex gap-3 justify-end">
                            <Button
                                variant="secondary"
                                onClick={() => setShowDeleteConfirm(false)}
                                disabled={deleting}
                                className="whitespace-nowrap"
                            >
                                取消
                            </Button>
                            <Button
                                variant="secondary"
                                onClick={handleDelete}
                                disabled={deleting}
                                isLoading={deleting}
                                startContent={<Trash2Icon className="w-4 h-4" />}
                                className="bg-red-50 hover:bg-red-100 text-red-700 dark:bg-red-950 dark:hover:bg-red-900 dark:text-red-400 border border-red-200 dark:border-red-800 whitespace-nowrap"
                            >
                                {deleting ? '删除中...' : '确认并删除'}
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
