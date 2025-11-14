'use client';
import { Button } from "@/components/ui/button";
import { Dropdown, DropdownItem, DropdownMenu, DropdownSection, DropdownTrigger, Spinner, Tooltip } from "@heroui/react";
import { useRef, useState, createContext, useContext, useCallback, forwardRef, useImperativeHandle, useEffect, Ref } from "react";
import { CopilotChatContext } from "../../../../src/entities/models/copilot";
import { CopilotMessage } from "../../../../src/entities/models/copilot";
import { Workflow } from "@/app/lib/types/workflow_types";
import { DataSource } from "@/src/entities/models/data-source";
import { z } from "zod";
import { Action as WorkflowDispatch } from "@/app/projects/[projectId]/workflow/workflow_editor";
import { Panel } from "@/components/common/panel-common";
import { ComposeBoxCopilot } from "@/components/common/compose-box-copilot";
import { Messages } from "./components/messages";
import { CopyIcon, CheckIcon, PlusIcon, XIcon, InfoIcon, Sparkles } from "lucide-react";
import { useCopilot } from "./use-copilot";
import { BillingUpgradeModal } from "@/components/common/billing-upgrade-modal";
import { SHOW_COPILOT_MARQUEE } from "@/app/lib/feature_flags";
import Image from "next/image";
import mascot from "@/public/mascot.png";

const CopilotContext = createContext<{
    workflow: z.infer<typeof Workflow> | null;
    dispatch: (action: any) => void;
}>({ workflow: null, dispatch: () => { } });

export function getAppliedChangeKey(messageIndex: number, actionIndex: number, field: string) {
    return `${messageIndex}-${actionIndex}-${field}`;
}

interface AppProps {
    projectId: string;
    workflow: z.infer<typeof Workflow>;
    dispatch: (action: any) => void;
    chatContext?: any;
    onCopyJson?: (data: { messages: any[] }) => void;
    onMessagesChange?: (messages: z.infer<typeof CopilotMessage>[]) => void;
    isInitialState?: boolean;
    dataSources?: z.infer<typeof DataSource>[];
}

const App = forwardRef<{ handleCopyChat: () => void; handleUserMessage: (message: string) => void }, AppProps>(function App({
    projectId,
    workflow,
    dispatch,
    chatContext = undefined,
    onCopyJson,
    onMessagesChange,
    isInitialState = false,
    dataSources,
}, ref) {
    

    const [messages, setMessages] = useState<z.infer<typeof CopilotMessage>[]>([]);
    const [discardContext, setDiscardContext] = useState(false);
    const [isLastInteracted, setIsLastInteracted] = useState(isInitialState);
    const workflowRef = useRef(workflow);
    const startRef = useRef<any>(null);
    const cancelRef = useRef<any>(null);
    const [statusBar, setStatusBar] = useState<any>(null);

    // Always use effectiveContext for the user's current selection
    const effectiveContext = discardContext ? null : chatContext;

    // Context locking state
    const [lockedContext, setLockedContext] = useState<any>(effectiveContext);
    const [pendingContext, setPendingContext] = useState<any>(effectiveContext);
    const [isStreaming, setIsStreaming] = useState(false);

    // Keep workflow ref up to date
    workflowRef.current = workflow;

    // Copilot streaming state
    const {
        streamingResponse,
        loading: loadingResponse,
        toolCalling,
        toolQuery,
        toolResult,
        error: responseError,
        clearError: clearResponseError,
        billingError,
        clearBillingError,
        start,
        cancel
    } = useCopilot({
        projectId,
        workflow: workflowRef.current,
        context: effectiveContext,
        dataSources: dataSources
    });

    // Store latest start/cancel functions in refs
    startRef.current = start;
    cancelRef.current = cancel;

    // Notify parent of message changes
    useEffect(() => {
        onMessagesChange?.(messages);
    }, [messages, onMessagesChange]);

    // Removed localStorage auto-start. Initial prompts are sent by parent via ref.

    // Reset discardContext when chatContext changes
    useEffect(() => {
        setDiscardContext(false);
    }, [chatContext]);

    // Memoized handleUserMessage for useImperativeHandle and hooks
    const handleUserMessage = useCallback((prompt: string) => {
        // Before starting streaming, lock the context to the current pendingContext
        setLockedContext(pendingContext);
        setMessages(currentMessages => [...currentMessages, {
            role: 'user',
            content: prompt
        }]);
        setIsLastInteracted(true);
    }, [setMessages, setIsLastInteracted, pendingContext, setLockedContext]);

    // Effect for getting copilot response
    useEffect(() => {
        if (!messages.length || messages.at(-1)?.role !== 'user') return;

        if (responseError) {
            return;
        }

        const currentStart = startRef.current;
        const currentCancel = cancelRef.current;

        if (currentStart) {
            currentStart(messages, (finalResponse: string) => {
                // Only add assistant message if there's content
                // If empty, the UI should handle it gracefully
                // 注意：流式响应已经在 Messages 组件中显示了，这里只需要在流结束时
                // 将最终响应添加到 messages 中（如果 streamingResponse 中没有的话）
                if (finalResponse && finalResponse.trim()) {
                    setMessages(prev => {
                        // 检查最后一条消息是否是助手消息且内容与 finalResponse 相同（避免重复）
                        const lastMessage = prev[prev.length - 1];
                        if (lastMessage?.role === 'assistant' && lastMessage.content === finalResponse) {
                            // 内容已存在，不重复添加
                            return prev;
                        }
                        // 添加新消息
                        return [
                            ...prev,
                            {
                                role: 'assistant',
                                content: finalResponse
                            }
                        ];
                    });
                } else {
                    // If no response, add a placeholder message or handle gracefully
                    console.warn('⚠️ Copilot returned empty response');
                    // Optionally add a message indicating no response
                    // setMessages(prev => [
                    //     ...prev,
                    //     {
                    //         role: 'assistant',
                    //         content: '抱歉，我没有生成任何回复。请重试。'
                    //     }
                    // ]);
                }
            });
        } else {
            // startRef not yet ready; no-op
        }

        return () => currentCancel();
    }, [messages, responseError]);

    // --- CONTEXT LOCKING LOGIC ---
    // Always update pendingContext to the latest effectiveContext
    useEffect(() => {
        setPendingContext(effectiveContext);
    }, [effectiveContext]);

    // Lock/unlock context based on streaming state
    useEffect(() => {
        if (loadingResponse) {
            // Streaming started: lock context to the value at the start
            setIsStreaming(true);
            setLockedContext((prev: any) => prev ?? pendingContext); // lock to previous if already set, else to pending
        } else {
            // Streaming ended: update lockedContext to the last pendingContext
            setIsStreaming(false);
            setLockedContext(pendingContext);
        }
    }, [loadingResponse, pendingContext]);

    // After streaming ends, update lockedContext live as effectiveContext changes
    useEffect(() => {
        if (!isStreaming) {
            setLockedContext(effectiveContext);
        }
        // If streaming, do not update lockedContext
    }, [effectiveContext, isStreaming]);
    // --- END CONTEXT LOCKING LOGIC ---

    const handleCopyChat = useCallback(() => {
        if (onCopyJson) {
            onCopyJson({
                messages,
            });
        }
    }, [messages, onCopyJson]);

    useImperativeHandle(ref, () => ({
        handleCopyChat,
        handleUserMessage
    }), [handleCopyChat, handleUserMessage]);

    // Memoized status bar change handler to prevent infinite update loop
    const handleStatusBarChange = useCallback((status: any) => {
        setStatusBar((prev: any) => {
            // Shallow compare previous and next status
            const next = { ...status, context: lockedContext, toolResult };
            const keys = Object.keys(next);
            if (
                prev &&
                keys.every(key => prev[key] === next[key])
            ) {
                return prev;
            }
            return next;
        });
    }, [lockedContext, toolResult]);

    return (
        <CopilotContext.Provider value={{ workflow: workflowRef.current, dispatch }}>
            <div className="h-full flex flex-col">
                <div className="flex-1 overflow-auto">
                    {messages.length === 0 && (
                        <div className="flex flex-col items-center justify-center py-4 pointer-events-none">
                            {/* Replace Sparkles icon with mascot image */}
                            <Image src={mascot} alt="质信智购吉祥物" width={160} height={160} className="object-contain mb-3 animate-float" />
                            
                            {/* Welcome/Intro Section */}
                            <div className="text-center max-w-md px-6 mb-3">
                                <h3 className="text-xl font-semibold text-zinc-700 dark:text-zinc-300 mb-2 text-center">
                                    👋 你好！
                                </h3>
                                <p className="text-base text-zinc-600 dark:text-zinc-400 mb-4 text-center">
                                    我是AI助手，帮助你构建智能体并添加工具。
                                </p>
                                <p className="text-base text-zinc-600 dark:text-zinc-400 mb-3 text-center">
                                    你可以在这里做什么：
                                </p>
                                <div className="space-y-2 max-w-2xl mx-auto text-left">
                                    <div className="flex items-start gap-3">
                                        <span className="text-lg">⚡</span>
                                        <span className="text-sm text-zinc-600 dark:text-zinc-400">使用自然语言快速构建AI智能体。</span>
                                    </div>
                                    <div className="flex items-start gap-3">
                                        <span className="text-lg">🔌</span>
                                        <span className="text-sm text-zinc-600 dark:text-zinc-400">通过一键集成连接工具。</span>
                                    </div>
                                    <div className="flex items-start gap-3">
                                        <span className="text-lg">📂</span>
                                        <span className="text-sm text-zinc-600 dark:text-zinc-400">通过添加文档为RAG提供知识支持。</span>
                                    </div>
                                    <div className="flex items-start gap-3">
                                        <span className="text-lg">🔄</span>
                                        <span className="text-sm text-zinc-600 dark:text-zinc-400">通过设置触发器和操作自动化工作流。</span>
                                    </div>
                                    <div className="flex items-start gap-3">
                                        <span className="text-lg">🚀</span>
                                        <span className="text-sm text-zinc-600 dark:text-zinc-400">通过API或SDK部署到任何地方。</span>
                                    </div>
                                </div>
                            </div>
                            
                            {SHOW_COPILOT_MARQUEE && (
                                <div className="relative mt-2 max-w-full px-8">
                                    <div className="font-mono text-sm whitespace-nowrap text-blue-400/60 dark:text-blue-500/40 font-small inline-flex">
                                        <div className="overflow-hidden w-0 animate-typing">What can I help you build?</div>
                                        <div className="border-r-2 border-blue-400 dark:border-blue-500 animate-cursor">&nbsp;</div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                    <Messages
                        messages={messages}
                        streamingResponse={streamingResponse}
                        loadingResponse={loadingResponse}
                        workflow={workflowRef.current}
                        dispatch={dispatch}
                        onStatusBarChange={handleStatusBarChange}
                        toolCalling={toolCalling}
                        toolQuery={toolQuery}
                        toolResult={toolResult}
                    />
                </div>
                <div className="shrink-0 px-0 pb-10">
                    {responseError && (
                        <div className="mb-4 p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex gap-2 justify-between items-center text-sm">
                            <p className="text-red-600 dark:text-red-400">{responseError}</p>
                            <Button
                                size="sm"
                                color="danger"
                                onClick={() => {
                                    // remove the last assistant message, if any
                                    setMessages(prev => {
                                        const lastMessage = prev[prev.length - 1];
                                        if (lastMessage?.role === 'assistant') {
                                            return prev.slice(0, -1);
                                        }
                                        return prev;
                                    });
                                    clearResponseError();
                                }}
                            >
                                Retry
                            </Button>
                        </div>
                    )}
                    <ComposeBoxCopilot
                        handleUserMessage={handleUserMessage}
                        messages={messages}
                        loading={loadingResponse}
                        initialFocus={isInitialState}
                        shouldAutoFocus={isLastInteracted}
                        onFocus={() => setIsLastInteracted(true)}
                        onCancel={cancel}
                        statusBar={statusBar || { context: lockedContext, toolResult }}
                    />
                </div>
            </div>
            <BillingUpgradeModal
                isOpen={!!billingError}
                onClose={clearBillingError}
                errorMessage={billingError || ''}
            />
        </CopilotContext.Provider>
    );
});

App.displayName = 'App';

export const Copilot = forwardRef<{ handleUserMessage: (message: string) => void }, {
    projectId: string;
    workflow: z.infer<typeof Workflow>;
    chatContext?: z.infer<typeof CopilotChatContext>;
    dispatch: (action: WorkflowDispatch) => void;
    isInitialState?: boolean;
    dataSources?: z.infer<typeof DataSource>[];
    activePanel?: 'playground' | 'copilot';
    onTogglePanel?: () => void;
}>(({
    projectId,
    workflow,
    chatContext = undefined,
    dispatch,
    isInitialState = false,
    dataSources,
    activePanel,
    onTogglePanel,
}, ref) => {
    // 开发模式下可能会多次挂载（React StrictMode），这是正常的
    useEffect(() => {
        console.log('🎪 Copilot wrapper component mounted:', {
            projectId,
            isInitialState,
            activePanel,
            chatContextType: chatContext?.type
        });
    }, [projectId, isInitialState, activePanel, chatContext?.type]);

    const [copilotKey, setCopilotKey] = useState(0);
    const [showCopySuccess, setShowCopySuccess] = useState(false);
    const [messages, setMessages] = useState<z.infer<typeof CopilotMessage>[]>([]);
    const [billingError, setBillingError] = useState<string | null>(null);
    const appRef = useRef<{ handleCopyChat: () => void; handleUserMessage: (message: string) => void }>(null);

    function handleNewChat() {
        setCopilotKey(prev => prev + 1);
        setMessages([]);
    }

    function handleCopyJson(data: { messages: any[] }) {
        const jsonString = JSON.stringify(data, null, 2);
        navigator.clipboard.writeText(jsonString);
        setShowCopySuccess(true);
        setTimeout(() => {
            setShowCopySuccess(false);
        }, 2000);
    }

    // Expose handleUserMessage through ref
    useImperativeHandle(ref, () => ({
        handleUserMessage: (message: string) => {
            const app = appRef.current as any;
            if (app?.handleUserMessage) {
                app.handleUserMessage(message);
            }
        }
    }), []);

    return (
        <>
            <Panel 
                variant="copilot"
                tourTarget="copilot"
                title={<div className="flex items-center gap-2 text-zinc-800 dark:text-zinc-200 font-semibold"><Sparkles className="w-4 h-4" /> Skipper</div>}
                subtitle="Build your assistant"
                rightActions={
                    <div className="flex items-center gap-2">
                        <Button
                            variant="primary"
                            size="sm"
                            onClick={handleNewChat}
                            className="bg-blue-50 text-blue-700 hover:bg-blue-100"
                            showHoverContent={true}
                            hoverContent="New chat"
                        >
                            <PlusIcon className="w-4 h-4" />
                        </Button>
                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => appRef.current?.handleCopyChat()}
                            showHoverContent={true}
                            hoverContent={showCopySuccess ? "Copied" : "Copy JSON"}
                        >
                            {showCopySuccess ? (
                                <CheckIcon className="w-4 h-4" />
                            ) : (
                                <CopyIcon className="w-4 h-4" />
                            )}
                        </Button>
                    </div>
                }
            >
                <div className="h-full overflow-auto px-3 pt-4">
                    <App
                        key={copilotKey}
                        ref={appRef}
                        projectId={projectId}
                        workflow={workflow}
                        dispatch={dispatch}
                        chatContext={chatContext}
                        onCopyJson={handleCopyJson}
                        onMessagesChange={setMessages}
                        isInitialState={isInitialState}
                        dataSources={dataSources}
                    />
                </div>
            </Panel>
        </>
    );
});

Copilot.displayName = 'Copilot';
