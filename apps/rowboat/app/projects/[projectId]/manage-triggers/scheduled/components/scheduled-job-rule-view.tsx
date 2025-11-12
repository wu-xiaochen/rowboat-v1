'use client';

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Spinner } from "@heroui/react";
import { Panel } from "@/components/common/panel-common";
import { fetchScheduledJobRule, deleteScheduledJobRule } from "@/app/actions/scheduled-job-rules.actions";
import { ScheduledJobRule } from "@/src/entities/models/scheduled-job-rule";
import { z } from "zod";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowLeftIcon, Trash2Icon } from "lucide-react";
import { MessageDisplay } from "@/app/lib/components/message-display";

export function ScheduledJobRuleView({ projectId, ruleId }: { projectId: string; ruleId: string; }) {
    const router = useRouter();
    const [rule, setRule] = useState<z.infer<typeof ScheduledJobRule> | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [deleting, setDeleting] = useState(false);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

    useEffect(() => {
        let ignore = false;
        (async () => {
            setLoading(true);
            const res = await fetchScheduledJobRule({ ruleId });
            if (ignore) return;
            setRule(res);
            setLoading(false);
        })();
        return () => { ignore = true; };
    }, [ruleId]);

    const title = useMemo(() => {
        if (!rule) return '计划任务规则';
        return `计划任务规则 ${rule.id}`;
    }, [rule]);

    const handleDelete = async () => {
        if (!rule) return;
        
        setDeleting(true);
        try {
            await deleteScheduledJobRule({
                projectId,
                ruleId: rule.id,
            });
            // Redirect back to job rules list
            router.push(`/projects/${projectId}/manage-triggers?tab=scheduled`);
        } catch (error) {
            console.error("Failed to delete rule:", error);
            alert("删除规则失败");
        } finally {
            setDeleting(false);
            setShowDeleteConfirm(false);
        }
    };

    const getStatusColor = (status: string, processedAt: string | null) => {
        if (processedAt) return 'text-green-600 dark:text-green-400';
        if (status === 'processing') return 'text-yellow-600 dark:text-yellow-400';
        if (status === 'triggered') return 'text-blue-600 dark:text-blue-400';
        return 'text-gray-600 dark:text-gray-400'; // pending
    };

    const getStatusText = (status: string, processedAt: string | null) => {
        if (processedAt) return '已完成';
        if (status === 'processing') return '处理中';
        if (status === 'triggered') return '已触发';
        return '等待中';
    };

    const formatDateTime = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleString();
    };

    return (
        <>
            <Panel
                title={
                    <div className="flex items-center gap-3">
                        <Link href={`/projects/${projectId}/manage-triggers?tab=scheduled`}>
                            <Button variant="secondary" size="sm" startContent={<ArrowLeftIcon className="w-4 h-4" />} className="whitespace-nowrap">
                                返回
                            </Button>
                        </Link>
                        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                            {title}
                        </div>
                    </div>
                }
                rightActions={
                    <div className="flex items-center gap-3">
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
                    <div className="max-w-[1024px] mx-auto">
                        {loading && (
                            <div className="flex items-center gap-2">
                                <Spinner size="sm" />
                                <div>加载中...</div>
                            </div>
                        )}
                        {!loading && rule && (
                            <div className="flex flex-col gap-6">
                                {/* Rule Metadata */}
                                <div className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                                    <div className="grid grid-cols-2 gap-4 text-sm">
                                        <div>
                                            <span className="font-semibold text-gray-700 dark:text-gray-300">规则ID：</span>
                                            <span className="ml-2 font-mono text-gray-600 dark:text-gray-400">{rule.id}</span>
                                        </div>
                                        <div>
                                            <span className="font-semibold text-gray-700 dark:text-gray-300">状态：</span>
                                            <span className={`ml-2 font-mono ${getStatusColor(rule.status, rule.processedAt || null)}`}>
                                                {getStatusText(rule.status, rule.processedAt || null)}
                                            </span>
                                        </div>
                                        <div>
                                            <span className="font-semibold text-gray-700 dark:text-gray-300">下次运行：</span>
                                            <span className="ml-2 font-mono text-gray-600 dark:text-gray-400">
                                                {formatDateTime(rule.nextRunAt)}
                                            </span>
                                        </div>
                                        <div>
                                            <span className="font-semibold text-gray-700 dark:text-gray-300">创建时间：</span>
                                            <span className="ml-2 font-mono text-gray-600 dark:text-gray-400">
                                                {formatDateTime(rule.createdAt)}
                                            </span>
                                        </div>
                                        {rule.processedAt && (
                                            <div>
                                                <span className="font-semibold text-gray-700 dark:text-gray-300">处理时间：</span>
                                                <span className="ml-2 font-mono text-gray-600 dark:text-gray-400">
                                                    {formatDateTime(rule.processedAt)}
                                                </span>
                                            </div>
                                        )}
                                        {rule.output?.jobId && (
                                            <div>
                                                <span className="font-semibold text-gray-700 dark:text-gray-300">任务ID：</span>
                                                <span className="ml-2 font-mono text-gray-600 dark:text-gray-400">
                                                    <Link 
                                                        href={`/projects/${projectId}/jobs/${rule.output.jobId}`}
                                                        className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                                                    >
                                                        {rule.output.jobId}
                                                    </Link>
                                                </span>
                                            </div>
                                        )}
                                        {rule.workerId && (
                                            <div>
                                                <span className="font-semibold text-gray-700 dark:text-gray-300">Worker ID：</span>
                                                <span className="ml-2 font-mono text-gray-600 dark:text-gray-400">{rule.workerId}</span>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Messages */}
                                <div className="space-y-4">
                                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                                        规则输入
                                    </h3>
                                    <div className="space-y-4">
                                        <div className="text-sm text-gray-600 dark:text-gray-400">
                                            消息 ({rule.input.messages.length})
                                        </div>
                                        {rule.input.messages.map((message, index) => (
                                            <div key={index} className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                                                <MessageDisplay message={message} index={index} />
                                            </div>
                                        ))}
                                    </div>
                                </div>
                                {rule.output && (
                                    <div className="space-y-4">
                                        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                                            规则输出
                                        </h3>
                                        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                                            {rule.output.jobId && (
                                                <div className="text-sm">
                                                    <span className="font-semibold text-gray-700 dark:text-gray-300">任务ID：</span>
                                                    <Link 
                                                        href={`/projects/${projectId}/jobs/${rule.output.jobId}`}
                                                        className="ml-2 text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                                                    >
                                                        {rule.output.jobId}
                                                    </Link>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                        {!loading && !rule && (
                            <div className="text-center text-gray-500 dark:text-gray-400">
                                未找到任务。
                            </div>
                        )}
                    </div>
                </div>
            </Panel>

            {/* Delete Confirmation Modal */}
            {showDeleteConfirm && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md mx-4">
                        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
                            删除计划任务规则
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                            确定要删除此计划任务规则吗？此操作无法撤销，将永久删除该规则及其所有相关数据。
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
                                {deleting ? '删除中...' : '删除'}
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
