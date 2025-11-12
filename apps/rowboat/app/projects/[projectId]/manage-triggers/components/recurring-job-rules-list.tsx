'use client';

import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, Spinner } from "@heroui/react";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/common/panel-common";
import { listRecurringJobRules, deleteRecurringJobRule } from "@/app/actions/recurring-job-rules.actions";
import { z } from "zod";
import { ListedRecurringRuleItem } from "@/src/application/repositories/recurring-job-rules.repository.interface";
import { isToday, isThisWeek, isThisMonth } from "@/lib/utils/date";
import { PlusIcon, Trash2, ArrowLeftIcon } from "lucide-react";
import { CreateRecurringJobRuleForm } from "./create-recurring-job-rule-form";

type ListedItem = z.infer<typeof ListedRecurringRuleItem>;

export function RecurringJobRulesList({ projectId }: { projectId: string }) {
    const [items, setItems] = useState<ListedItem[]>([]);
    const [cursor, setCursor] = useState<string | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [loadingMore, setLoadingMore] = useState<boolean>(false);
    const [hasMore, setHasMore] = useState<boolean>(false);
    const [deletingRule, setDeletingRule] = useState<string | null>(null);
    const [showCreateForm, setShowCreateForm] = useState<boolean>(false);

    const fetchPage = useCallback(async (cursorArg?: string | null) => {
        const res = await listRecurringJobRules({ projectId, cursor: cursorArg ?? undefined, limit: 20 });
        return res;
    }, [projectId]);

    useEffect(() => {
        let ignore = false;
        (async () => {
            setLoading(true);
            const res = await fetchPage(null);
            if (ignore) return;
            setItems(res.items);
            setCursor(res.nextCursor);
            setHasMore(Boolean(res.nextCursor));
            setLoading(false);
        })();
        return () => { ignore = true; };
    }, [fetchPage]);

    useEffect(() => {
        if (!loading && items.length === 0 && !showCreateForm) {
            setShowCreateForm(true);
        }
    }, [loading, items.length, showCreateForm]);

    const loadMore = useCallback(async () => {
        if (!cursor) return;
        setLoadingMore(true);
        const res = await fetchPage(cursor);
        setItems(prev => [...prev, ...res.items]);
        setCursor(res.nextCursor);
        setHasMore(Boolean(res.nextCursor));
        setLoadingMore(false);
    }, [cursor, fetchPage]);

    const handleCreateNew = () => {
        setShowCreateForm(true);
    };

    const handleBackToList = () => {
        setShowCreateForm(false);
        // Reload the list in case new triggers were created
        const reload = async () => {
            setLoading(true);
            const res = await fetchPage(null);
            setItems(res.items);
            setCursor(res.nextCursor);
            setHasMore(Boolean(res.nextCursor));
            setLoading(false);
        };
        reload();
    };

    const handleDeleteRule = async (ruleId: string) => {
        if (!window.confirm('确定要删除此重复触发器吗？')) {
            return;
        }

        try {
            setDeletingRule(ruleId);
            await deleteRecurringJobRule({ projectId, ruleId });
            // Remove the deleted item from the list
            setItems(prev => prev.filter(item => item.id !== ruleId));
        } catch (err: any) {
            console.error('Error deleting recurring trigger:', err);
            alert('删除重复触发器失败。请重试。');
        } finally {
            setDeletingRule(null);
        }
    };

    const sections = useMemo(() => {
        const groups: Record<string, ListedItem[]> = {
            今天: [],
            本周: [],
            本月: [],
            更早: [],
        };
        for (const item of items) {
            const d = new Date(item.nextRunAt);
            if (isToday(d)) groups['今天'].push(item);
            else if (isThisWeek(d)) groups['本周'].push(item);
            else if (isThisMonth(d)) groups['本月'].push(item);
            else groups['更早'].push(item);
        }
        return groups;
    }, [items]);

    const getStatusColor = (disabled: boolean, lastError: string | null) => {
        if (disabled) return 'text-red-600 dark:text-red-400';
        if (lastError) return 'text-yellow-600 dark:text-yellow-400';
        return 'text-green-600 dark:text-green-400';
    };

    const getStatusText = (disabled: boolean, lastError: string | null) => {
        if (disabled) return '已禁用';
        if (lastError) return '错误';
        return '激活';
    };

    const formatNextRunAt = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleString();
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

    if (showCreateForm) {
        return <CreateRecurringJobRuleForm projectId={projectId} onBack={handleBackToList} hasExistingTriggers={items.length > 0} />;
    }

    return (
        <Panel
            title={
                <div className="text-base font-normal text-gray-900 dark:text-gray-100">
                    在自动化重复计划（cron任务）上运行您的助手工作流。
                </div>
            }
            rightActions={
                <div className="flex items-center gap-3">
                    <Button 
                        size="sm" 
                        className="whitespace-nowrap" 
                        startContent={<PlusIcon className="w-4 h-4" />}
                        onClick={handleCreateNew}
                    >
                        新建重复触发器
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
                    {!loading && (
                        <div className="flex flex-col gap-6">
                            {Object.entries(sections).map(([sectionName, sectionItems]) => {
                                if (sectionItems.length === 0) return null;
                                return (
                                    <div key={sectionName} className="space-y-3">
                                        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                                            {sectionName}
                                        </h3>
                                        <div className="grid gap-3">
                                            {sectionItems.map((item) => (
                                                <div
                                                    key={item.id}
                                                    className="block p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 transition-colors"
                                                >
                                                    <div className="flex items-start justify-between">
                                                        <div className="flex-1">
                                                            <Link
                                                                href={`/projects/${projectId}/manage-triggers/recurring/${item.id}`}
                                                                className="block"
                                                            >
                                                                <div className="flex items-center gap-3 mb-2">
                                                                    <span className={`text-sm font-medium ${getStatusColor(item.disabled, item.lastError || null)}`}>
                                                                        {getStatusText(item.disabled, item.lastError || null)}
                                                                    </span>
                                                                    <span className="text-sm text-gray-500 dark:text-gray-400">
                                                                        下次运行: {formatNextRunAt(item.nextRunAt)}
                                                                    </span>
                                                                </div>
                                                                <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                                                                    计划: {formatCronExpression(item.cron)}
                                                                </div>
                                                                <div className="text-sm text-gray-600 dark:text-gray-400">
                                                                    创建时间: {new Date(item.createdAt).toLocaleDateString()}
                                                                </div>
                                                                {item.lastError && (
                                                                    <div className="text-sm text-red-600 dark:text-red-400 mt-1">
                                                                        最后错误: {item.lastError}
                                                                    </div>
                                                                )}
                                                            </Link>
                                                        </div>
                                                        <Button
                                                            variant="tertiary"
                                                            size="sm"
                                                            isLoading={deletingRule === item.id}
                                                            onClick={() => handleDeleteRule(item.id)}
                                                            className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:text-red-400 dark:hover:text-red-300 dark:hover:bg-red-950"
                                                        >
                                                            <Trash2 className="w-4 h-4" />
                                                        </Button>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                );
                            })}
                            {items.length === 0 && !loading && (
                                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                                    还没有重复触发器。创建您的第一个重复触发器以开始。
                                </div>
                            )}
                            {hasMore && (
                                <div className="text-center">
                                    <Button
                                        onClick={loadMore}
                                        disabled={loadingMore}
                                        variant="secondary"
                                        size="sm"
                                        isLoading={loadingMore}
                                        className="whitespace-nowrap"
                                    >
                                        {loadingMore ? '加载中...' : '加载更多'}
                                    </Button>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </Panel>
    );
}
