'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Spinner, Link } from '@heroui/react';
import { Button } from '@/components/ui/button';
import { Panel } from '@/components/common/panel-common';
import { Plus, Trash2, ZapIcon, ChevronDown, ChevronUp, ArrowLeftIcon } from 'lucide-react';
import Image from 'next/image';
import { z } from 'zod';
import { ComposioTriggerDeployment } from '@/src/entities/models/composio-trigger-deployment';
import { ComposioTriggerType } from '@/src/entities/models/composio-trigger-type';
import { isToday, isThisWeek, isThisMonth } from '@/lib/utils/date';
import { listComposioTriggerDeployments, deleteComposioTriggerDeployment, createComposioTriggerDeployment } from '@/app/actions/composio.actions';
import { SelectComposioToolkit } from '../../tools/components/SelectComposioToolkit';
import { ComposioTriggerTypesPanel } from '../../workflow/components/ComposioTriggerTypesPanel';
import { TriggerConfigForm } from '../../workflow/components/TriggerConfigForm';
import { ToolkitAuthModal } from '../../tools/components/ToolkitAuthModal';
import { ZToolkit } from "@/src/application/lib/composio/types";
import { Project } from "@/src/entities/models/project";
import { fetchProject } from '@/app/actions/project.actions';

type TriggerDeployment = z.infer<typeof ComposioTriggerDeployment>;

// Removed friendly name computation; backend now provides friendly trigger name

export function TriggersTab({ projectId }: { projectId: string }) {
  const [triggers, setTriggers] = useState<TriggerDeployment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateFlow, setShowCreateFlow] = useState(false);
  const [selectedToolkit, setSelectedToolkit] = useState<z.infer<typeof ZToolkit> | null>(null);
  const [selectedTriggerType, setSelectedTriggerType] = useState<z.infer<typeof ComposioTriggerType> | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [isSubmittingTrigger, setIsSubmittingTrigger] = useState(false);
  const [deletingTrigger, setDeletingTrigger] = useState<string | null>(null);
  const [projectConfig, setProjectConfig] = useState<z.infer<typeof Project> | null>(null);
  const [expandedTrigger, setExpandedTrigger] = useState<string | null>(null);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState<boolean>(false);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);

  const loadProjectConfig = useCallback(async () => {
    try {
      const config = await fetchProject(projectId);
      setProjectConfig(config);
    } catch (err: any) {
      console.error('Error fetching project config:', err);
    }
  }, [projectId]);

  const sections = useMemo(() => {
    const groups: Record<string, TriggerDeployment[]> = {
      今天: [],
      本周: [],
      本月: [],
      更早: [],
    };
    for (const trigger of triggers) {
      const d = new Date(trigger.createdAt);
      if (isToday(d)) groups['今天'].push(trigger);
      else if (isThisWeek(d)) groups['本周'].push(trigger);
      else if (isThisMonth(d)) groups['本月'].push(trigger);
      else groups['更早'].push(trigger);
    }
    return groups;
  }, [triggers]);

  const loadTriggers = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await listComposioTriggerDeployments({ projectId });
      setTriggers(response.items);
      setCursor(response.nextCursor);
      setHasMore(Boolean(response.nextCursor));
    } catch (err: any) {
      console.error('Error loading triggers:', err);
      setError('加载触发器失败。请重试。');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  const loadMore = useCallback(async () => {
    if (!cursor) return;
    setLoadingMore(true);
    try {
      const response = await listComposioTriggerDeployments({ projectId, cursor });
      setTriggers(prev => [...prev, ...response.items]);
      setCursor(response.nextCursor);
      setHasMore(Boolean(response.nextCursor));
    } catch (err: any) {
      console.error('Error loading more triggers:', err);
    } finally {
      setLoadingMore(false);
    }
  }, [cursor, projectId]);

  const handleDeleteTrigger = async (deploymentId: string) => {
    if (!window.confirm('确定要删除此触发器吗？')) {
      return;
    }

    try {
      setDeletingTrigger(deploymentId);
      await deleteComposioTriggerDeployment({ projectId, deploymentId });
      await loadTriggers(); // Reload the list
    } catch (err: any) {
      console.error('Error deleting trigger:', err);
      setError('删除触发器失败。请重试。');
    } finally {
      setDeletingTrigger(null);
    }
  };

  const handleCreateNew = () => {
    setShowCreateFlow(true);
  };

  const handleBackToList = () => {
    setShowCreateFlow(false);
    setSelectedToolkit(null);
    setSelectedTriggerType(null);
    setShowAuthModal(false);
    setIsSubmittingTrigger(false);
    setExpandedTrigger(null); // Reset expanded state
    loadTriggers(); // Reload in case any triggers were created
  };

  const handleSelectToolkit = (toolkit: z.infer<typeof ZToolkit>) => {
    setSelectedToolkit(toolkit);
  };

  const handleBackToToolkitSelection = () => {
    setSelectedToolkit(null);
    setSelectedTriggerType(null);
    setIsSubmittingTrigger(false);
  };

  const handleSelectTriggerType = (triggerType: z.infer<typeof ComposioTriggerType>) => {
    if (!selectedToolkit) return;
    
    setSelectedTriggerType(triggerType);
    
    // Check if toolkit requires auth and if connected account exists
    const needsAuth = !selectedToolkit.no_auth;
    const hasConnection = projectConfig?.composioConnectedAccounts?.[selectedToolkit.slug]?.status === 'ACTIVE';
    
    if (needsAuth && !hasConnection) {
      // Show auth modal
      setShowAuthModal(true);
    } else {
      // Proceed to trigger configuration
      // For now this is just the placeholder, but will be actual config later
    }
  };

  const handleAuthComplete = async () => {
    setShowAuthModal(false);
    await loadProjectConfig(); // Refresh project config
  };

  const handleTriggerSubmit = async (triggerConfig: Record<string, unknown>) => {
    if (!selectedToolkit || !selectedTriggerType) return;

    try {
      setIsSubmittingTrigger(true);
      
      // Get the connected account ID for this toolkit
      const connectedAccountId = projectConfig?.composioConnectedAccounts?.[selectedToolkit.slug]?.id;
      
      if (!connectedAccountId) {
        throw new Error('未找到此工具包的连接账户');
      }

      // Create the trigger deployment
      await createComposioTriggerDeployment({
        projectId,
        triggerTypeSlug: selectedTriggerType.slug,
        connectedAccountId,
        triggerConfig,
      });

      // Success! Go back to triggers list tab and reload
      if (typeof window !== 'undefined') {
        window.location.href = `/projects/${projectId}/manage-triggers?tab=triggers`;
        return;
      }
      handleBackToList();
    } catch (err: any) {
      console.error('Error creating trigger:', err);
      setError('创建触发器失败。请重试。');
    } finally {
      setIsSubmittingTrigger(false);
    }
  };

  useEffect(() => {
    loadProjectConfig();
  }, [loadProjectConfig]);

  useEffect(() => {
    if (!showCreateFlow) {
      loadTriggers();
    }
  }, [showCreateFlow, loadTriggers]);

  useEffect(() => {
    if (!loading && !error && triggers.length === 0 && !showCreateFlow) {
      setShowCreateFlow(true);
    }
  }, [loading, error, triggers.length, showCreateFlow]);

  useEffect(() => {
    // No-op: trigger names are now derived from slug locally
  }, [triggers]);

  const renderTriggerList = () => {
    if (loading) {
      return (
        <Panel
          title={
            <div className="text-base font-normal text-gray-900 dark:text-gray-100">
              正在加载您的触发器
            </div>
          }
        >
          <div className="h-full overflow-auto px-4 py-4">
            <div className="max-w-[1024px] mx-auto">
              <div className="flex items-center justify-center py-8">
                <Spinner size="lg" />
                <span className="ml-2">加载触发器中...</span>
              </div>
            </div>
          </div>
        </Panel>
      );
    }

    if (error) {
      return (
        <Panel
          title={
            <div className="text-base font-normal text-gray-900 dark:text-gray-100">
              加载触发器时出错
            </div>
          }
          rightActions={
            <Button variant="secondary" onClick={loadTriggers} className="whitespace-nowrap">
              重试
            </Button>
          }
        >
          <div className="h-full overflow-auto px-4 py-4">
            <div className="max-w-[1024px] mx-auto">
              <div className="text-center py-8">
                <p className="text-red-500 mb-4">{error}</p>
              </div>
            </div>
          </div>
        </Panel>
      );
    }

    if (triggers.length === 0) {
      return (
        <Panel
          title={
            <div className="text-base font-normal text-gray-900 dark:text-gray-100">
              监听来自连接应用的事件，以自动运行您的助手工作流。
            </div>
          }
          rightActions={
            <Button
              variant="primary"
              startContent={<Plus className="w-4 h-4" />}
              onClick={handleCreateNew}
              className="whitespace-nowrap"
            >
              新建外部触发器
            </Button>
          }
        >
          <div className="h-full overflow-auto px-4 py-4">
            <div className="max-w-[1024px] mx-auto">
              <div className="text-center py-12">
                <ZapIcon className="w-16 h-16 mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                  还没有外部触发器
                </h3>
                <p className="text-gray-500 dark:text-gray-400 mb-6">
                  创建您的第一个外部触发器以监听来自连接应用的事件。
                </p>
              </div>
            </div>
          </div>
        </Panel>
      );
    }

    return (
      <Panel
        title={
          <div className="text-base font-normal text-gray-900 dark:text-gray-100">
            监听来自连接应用的事件，以自动运行您的助手工作流。
          </div>
        }
        rightActions={
          <Button
            variant="primary"
            startContent={<Plus className="w-4 h-4" />}
            onClick={handleCreateNew}
            className="whitespace-nowrap"
          >
            新建外部触发器
          </Button>
        }
      >
        <div className="h-full overflow-auto px-4 py-4">
          <div className="max-w-[1024px] mx-auto">
            <div className="flex flex-col gap-6">
              {Object.entries(sections).map(([sectionName, sectionTriggers]) => {
                if (sectionTriggers.length === 0) return null;
                return (
                  <div key={sectionName} className="space-y-3">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      {sectionName}
                    </h3>
                    <div className="grid gap-3">
                      {sectionTriggers.map((trigger) => (
                        <div
                          key={trigger.id}
                          className="block p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 transition-colors"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <a href={`/projects/${projectId}/manage-triggers/triggers/${trigger.id}`} className="block">
                                <div className="flex items-center gap-3 mb-1">
                                  {trigger.logo && (
                                    <Image
                                      src={trigger.logo}
                                      alt={`${trigger.toolkitSlug} logo`}
                                      width={20}
                                      height={20}
                                      className="rounded"
                                      unoptimized
                                    />
                                  )}
                                  {trigger.toolkitSlug && (
                                    <span className="text-xs px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-900 text-gray-600 dark:text-gray-400">
                                      {trigger.toolkitSlug}
                                    </span>
                                  )}
                                </div>
                                <div className="h-2" />
                                <div className="flex items-center gap-2 mb-2">
                                  <span className="text-sm font-medium text-green-600 dark:text-green-400">激活</span>
                                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                    {trigger.triggerTypeName}
                                  </span>
                                </div>
                                <div className="text-sm text-gray-500 dark:text-gray-400">
                                  创建时间: {new Date(trigger.createdAt).toLocaleDateString()}
                                </div>
                                {Object.keys(trigger.triggerConfig).length > 0 && (
                                  <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                    配置: {Object.keys(trigger.triggerConfig).length} 个设置
                                  </div>
                                )}
                              </a>
                            </div>
                            <Button
                              variant="tertiary"
                              size="sm"
                              isLoading={deletingTrigger === trigger.id}
                              onClick={() => handleDeleteTrigger(trigger.id)}
                              startContent={<Trash2 className="w-4 h-4" />}
                              className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:text-red-400 dark:hover:text-red-300 dark:hover:bg-red-950"
                            />
                          </div>
                          
                          {/* Advanced Details Section - Collapsible */}
                          <div className="mt-3">
                            <button
                              onClick={() => setExpandedTrigger(expandedTrigger === trigger.id ? null : trigger.id)}
                              className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
                            >
                              <span className="font-medium">高级详情</span>
                              {expandedTrigger === trigger.id ? (
                                <ChevronUp className="w-3 h-3" />
                              ) : (
                                <ChevronDown className="w-3 h-3" />
                              )}
                            </button>
                            
                            {expandedTrigger === trigger.id && (
                              <div className="mt-2 space-y-1">
                                <div className="text-xs text-gray-600 dark:text-gray-400">
                                  <span className="font-medium">Slug：</span> {trigger.triggerTypeSlug}
                                </div>
                                <div className="text-xs text-gray-600 dark:text-gray-400">
                                  <span className="font-medium">触发器ID：</span> {trigger.triggerId}
                                </div>
                                <div className="text-xs text-gray-600 dark:text-gray-400">
                                  <span className="font-medium">连接账户：</span> {trigger.connectedAccountId}
                                </div>
                                
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
              
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
          </div>
        </div>
      </Panel>
    );
  };

  const renderCreateFlow = () => {
    // If trigger type is selected and auth is complete, show config
    if (selectedToolkit && selectedTriggerType && !showAuthModal) {
      const needsAuth = !selectedToolkit.no_auth;
      const hasConnection = projectConfig?.composioConnectedAccounts?.[selectedToolkit.slug]?.status === 'ACTIVE';
      
      if (!needsAuth || hasConnection) {
        return (
          <TriggerConfigForm
            toolkit={selectedToolkit}
            triggerType={selectedTriggerType}
            onBack={handleBackToToolkitSelection}
            onSubmit={handleTriggerSubmit}
            isSubmitting={isSubmittingTrigger}
          />
        );
      }
    }

    // If no toolkit selected, show toolkit selection
    if (!selectedToolkit) {
      return (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                选择工具包以创建触发器
              </h3>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                注意：触发器仅在已发布的工作流版本上运行。发布任何更改以使它们激活。
              </p>
            </div>
            {triggers.length > 0 && (
              <Button
                variant="secondary"
                onClick={handleBackToList}
                startContent={<ArrowLeftIcon className="w-4 h-4" />}
                className="whitespace-nowrap"
              >
                返回触发器
              </Button>
            )}
          </div>

          <SelectComposioToolkit
            projectId={projectId}
            tools={[]} // Empty array since we're not using this for tools
            onSelectToolkit={handleSelectToolkit}
            initialToolkitSlug={null}
            filterByTriggers={true}
          />
        </div>
      );
    }

    // If toolkit selected, show trigger types
    return (
      <div className="space-y-4">
        <ComposioTriggerTypesPanel
          toolkit={selectedToolkit}
          onBack={handleBackToToolkitSelection}
          onSelectTriggerType={handleSelectTriggerType}
        />
      </div>
    );
  };

  return (
    <>
      {showCreateFlow ? renderCreateFlow() : renderTriggerList()}
      
      {/* Auth Modal */}
      {selectedToolkit && (
        <ToolkitAuthModal
          isOpen={showAuthModal}
          onClose={() => setShowAuthModal(false)}
          toolkitSlug={selectedToolkit.slug}
          projectId={projectId}
          onComplete={handleAuthComplete}
        />
      )}
    </>
  );
}
