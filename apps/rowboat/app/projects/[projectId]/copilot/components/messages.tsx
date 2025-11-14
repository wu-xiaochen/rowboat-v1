'use client';
import { Spinner } from "@heroui/react";
import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import { z } from "zod";
import { Workflow} from "@/app/lib/types/workflow_types";
import MarkdownContent from "@/app/lib/components/markdown-content";
import { MessageSquareIcon, EllipsisIcon, XIcon, CheckCheckIcon, ChevronDown, ChevronUp } from "lucide-react";
import { CopilotMessage, CopilotAssistantMessage, CopilotAssistantMessageActionPart } from "@/src/entities/models/copilot";
import { Action, StreamingAction } from './actions';
import { useParsedBlocks } from "../use-parsed-blocks";
import { validateConfigChanges } from "@/app/lib/client_utils";
import { PreviewModalProvider } from '../../workflow/preview-modal';
import { createAtMentions } from "@/app/lib/components/atmentions";

const CopilotResponsePart = z.union([
    z.object({
        type: z.literal('text'),
        content: z.string(),
    }),
    z.object({
        type: z.literal('streaming_action'),
        action: CopilotAssistantMessageActionPart.shape.content.partial(),
    }),
    z.object({
        type: z.literal('action'),
        action: CopilotAssistantMessageActionPart.shape.content,
    }),
]);

function enrich(response: string): z.infer<typeof CopilotResponsePart> {
    // Debug: Log the response to understand what we're receiving
    console.log('🔍 [enrich] 处理内容:', {
        length: response.length,
        preview: response.substring(0, 100),
        startsWithDoubleSlash: response.trim().startsWith('//'),
        firstLines: response.trim().split('\n').slice(0, 3)
    });
    
    // If it's not a code block, return as text
    if (!response.trim().startsWith('//')) {
        console.log('⚠️ [enrich] 不是代码块格式（不以 // 开头），返回文本');
        return {
            type: 'text',
            content: response
        };
    }

    // Parse the metadata from comments
    const lines = response.trim().split('\n');
    const metadata: Record<string, string> = {};
    let jsonStartIndex = 0;

    // Parse metadata from comment lines
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line.startsWith('//')) {
            jsonStartIndex = i;
            break;
        }
        const [key, value] = line.substring(2).trim().split(':').map(s => s.trim());
        if (key && value) {
            metadata[key] = value;
        }
    }

    // Try to parse the JSON part
    try {
        const jsonContent = lines.slice(jsonStartIndex).join('\n');
        
        // 检查JSON是否完整（流式输出时可能不完整）
        // 更严格的检查：确保JSON字符串是完整的（考虑字符串内的转义字符）
        let openBraces = 0;
        let closeBraces = 0;
        let inString = false;
        let escapeNext = false;
        
        for (let i = 0; i < jsonContent.length; i++) {
            const char = jsonContent[i];
            
            if (escapeNext) {
                escapeNext = false;
                continue;
            }
            
            if (char === '\\') {
                escapeNext = true;
                continue;
            }
            
            if (char === '"') {
                inString = !inString;
                continue;
            }
            
            if (!inString) {
                if (char === '{') openBraces++;
                if (char === '}') closeBraces++;
            }
        }
        
        // 如果JSON不完整（流式输出中），返回streaming_action
        if (openBraces > closeBraces || inString) {
            console.log('⚠️ [enrich] JSON不完整（流式输出中），返回streaming_action', {
                openBraces,
                closeBraces,
                inString,
                jsonLength: jsonContent.length
            });
            return {
                type: 'streaming_action',
                action: {
                    action: (metadata.action as 'create_new' | 'edit' | 'delete') || undefined,
                    config_type: (metadata.config_type as 'tool' | 'agent' | 'prompt' | 'pipeline' | 'start_agent') || undefined,
                    name: metadata.name
                }
            };
        }
        
        const jsonData = JSON.parse(jsonContent);

        // If we have all required metadata, validate the config changes
        if (metadata.action && metadata.config_type && metadata.name) {
            const result = validateConfigChanges(
                metadata.config_type,
                jsonData.config_changes || {},
                metadata.name
            );

            if ('error' in result) {
                return {
                    type: 'action',
                    action: {
                        action: metadata.action as 'create_new' | 'edit' | 'delete',
                        config_type: metadata.config_type as 'tool' | 'agent' | 'prompt' | 'pipeline' | 'start_agent',
                        name: metadata.name,
                        change_description: jsonData.change_description || '',
                        config_changes: {},
                        error: result.error
                    }
                };
            }

            return {
                type: 'action',
                action: {
                    action: metadata.action as 'create_new' | 'edit' | 'delete',
                    config_type: metadata.config_type as 'tool' | 'agent' | 'prompt' | 'pipeline' | 'start_agent',
                    name: metadata.name,
                    change_description: jsonData.change_description || '',
                    config_changes: result.changes
                }
            };
        }
    } catch (e) {
        // JSON parsing failed - this is likely a streaming block
        console.warn('⚠️ [enrich] JSON 解析失败:', e);
        console.warn('⚠️ [enrich] 尝试解析的内容:', lines.slice(jsonStartIndex).join('\n').substring(0, 200));
    }

    // Return as streaming action with whatever metadata we have
    return {
        type: 'streaming_action',
        action: {
            action: (metadata.action as 'create_new' | 'edit' | 'delete') || undefined,
            config_type: (metadata.config_type as 'tool' | 'agent' | 'prompt' | 'pipeline' | 'start_agent') || undefined,
            name: metadata.name
        }
    };
}

function UserMessage({ content }: { content: string }) {
    return (
        <div className="w-full">
            <div className="bg-blue-50 dark:bg-[#1e2023] px-4 py-2.5 
                rounded-lg text-sm leading-relaxed
                text-gray-700 dark:text-gray-200 
                border border-blue-100 dark:border-[#2a2d31]
                shadow-sm animate-[slideUpAndFade_150ms_ease-out]">
                <div className="text-left">
                    <MarkdownContent content={content} />
                </div>
            </div>
        </div>
    );
}

function InternalAssistantMessage({ content }: { content: string }) {
    const [expanded, setExpanded] = useState(false);

    return (
        <div className="w-full">
            {!expanded ? (
                <button className="flex items-center text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 gap-1 group"
                    onClick={() => setExpanded(true)}>
                    <MessageSquareIcon size={16} />
                    <EllipsisIcon size={16} />
                    <span className="text-xs">Show debug message</span>
                </button>
            ) : (
                <div className="w-full">
                    <div className="border border-gray-200 dark:border-gray-700 border-dashed 
                        px-4 py-2.5 rounded-lg text-sm
                        text-gray-700 dark:text-gray-200 shadow-sm">
                        <div className="flex justify-end mb-2">
                            <button className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                                onClick={() => setExpanded(false)}>
                                <XIcon size={16} />
                            </button>
                        </div>
                        <pre className="whitespace-pre-wrap">{content}</pre>
                    </div>
                </div>
            )}
        </div>
    );
}



/**
 * AssistantMessage component that renders copilot responses with action cards.
 * 
 * Features:
 * - Renders text content with markdown support
 * - Displays individual action cards for workflow changes
 * - Shows "Apply All" button when there are action cards
 * - Supports streaming responses with real-time apply all functionality
 * - Action cards are in a collapsible panel with a ticker summary in collapsed state
 */
function AssistantMessage({
    content,
    workflow,
    dispatch,
    messageIndex,
    loading,
    onStatusBarChange
}: {
    content: z.infer<typeof CopilotAssistantMessage>['content'],
    workflow: z.infer<typeof Workflow>,
    dispatch: (action: any) => void,
    messageIndex: number,
    loading: boolean,
    onStatusBarChange?: (status: any) => void
}) {
    const blocks = useParsedBlocks(content);
    const [appliedActions, setAppliedActions] = useState<Set<number>>(new Set());
    // Remove autoApplyEnabled and useEffect for auto-apply

    // parse actions from parts
    const parsed = useMemo(() => {
        const result: z.infer<typeof CopilotResponsePart>[] = [];
        for (const block of blocks) {
            if (block.type === 'text') {
                result.push({
                    type: 'text',
                    content: block.content,
                });
            } else {
                result.push(enrich(block.content));
            }
        }
        return result;
    }, [blocks]);

    // Create atValues for markdown mentions (includes existing workflow entities + pending actions)
    const atValues = useMemo(() => {
        // Collect all agents that will exist (existing + pending actions, including streaming actions)
        const allAgents = [...workflow.agents];
        parsed.forEach((part) => {
            // 包含 action 和 streaming_action 中的智能体
            if ((part.type === 'action' || part.type === 'streaming_action') && 
                part.action.config_type === 'agent' && 
                (part.action.action === 'create_new' || part.action.action === 'edit')) {
                // This agent is being created or edited, add it to the list
                const agentName = part.action.name;
                if (agentName && !allAgents.some(a => a.name === agentName)) {
                    allAgents.push({
                        name: agentName,
                        disabled: false,
                        type: (part.type === 'action' && part.action.config_changes) 
                            ? (part.action.config_changes as any)?.type || 'conversation'
                            : 'conversation',
                    } as any);
                }
            }
        });
        
        return createAtMentions({
            agents: allAgents,
            prompts: workflow.prompts || [],
            tools: workflow.tools || [],
            pipelines: workflow.pipelines || [],
        });
    }, [workflow, parsed]);

    // Count action cards for tracking
    const actionParts = parsed.filter(part => part.type === 'action' || part.type === 'streaming_action');
    const totalActions = parsed.filter(part => part.type === 'action').length;
    const appliedCount = Array.from(appliedActions).length;
    const pendingCount = Math.max(0, totalActions - appliedCount);
    const allApplied = pendingCount === 0 && totalActions > 0;

    // Memoized applyAction for useCallback dependencies
    const applyAction = useCallback((action: any, actionIndex: number) => {
        // Only apply, do not update appliedActions here
        if (action.action === 'create_new') {
            switch (action.config_type) {
                case 'agent': {
                    // Prevent duplicate agent names
                    if (workflow.agents.some((agent: any) => agent.name === action.name)) {
                        return;
                    }
                    dispatch({
                        type: 'add_agent',
                        agent: {
                            name: action.name,
                            ...action.config_changes
                        },
                        fromCopilot: true
                    });
                    break;
                }
                case 'tool': {
                    // Prevent duplicate tool names
                    if (workflow.tools.some((tool: any) => tool.name === action.name)) {
                        return;
                    }
                    dispatch({
                        type: 'add_tool',
                        tool: {
                            name: action.name,
                            ...action.config_changes
                        },
                        fromCopilot: true
                    });
                    break;
                }
                case 'prompt':
                    dispatch({
                        type: 'add_prompt',
                        prompt: {
                            name: action.name,
                            ...action.config_changes
                        },
                        fromCopilot: true
                    });
                    break;
                case 'pipeline':
                    dispatch({
                        type: 'add_pipeline',
                        pipeline: {
                            name: action.name,
                            ...action.config_changes
                        },
                        fromCopilot: true
                    });
                    break;
            }
        } else if (action.action === 'edit') {
            switch (action.config_type) {
                case 'agent':
                    dispatch({
                        type: 'update_agent_no_select',
                        name: action.name,
                        agent: action.config_changes
                    });
                    break;
                case 'tool':
                    dispatch({
                        type: 'update_tool_no_select',
                        name: action.name,
                        tool: action.config_changes
                    });
                    break;
                case 'prompt':
                    dispatch({
                        type: 'update_prompt',
                        name: action.name,
                        prompt: action.config_changes
                    });
                    break;
                case 'pipeline':
                    dispatch({
                        type: 'update_pipeline',
                        name: action.name,
                        pipeline: action.config_changes
                    });
                    break;
                case 'start_agent':
                    dispatch({
                        type: 'set_main_agent',
                        name: action.name,
                    })
                    break;
            }
        } else if (action.action === 'delete') {
            switch (action.config_type) {
                case 'agent':
                    dispatch({
                        type: 'delete_agent',
                        name: action.name
                    });
                    break;
                case 'tool':
                    dispatch({
                        type: 'delete_tool',
                        name: action.name
                    });
                    break;
                case 'prompt':
                    dispatch({
                        type: 'delete_prompt',
                        name: action.name
                    });
                    break;
                case 'pipeline':
                    dispatch({
                        type: 'delete_pipeline',
                        name: action.name
                    });
                    break;
            }
        }
    }, [dispatch, workflow.agents, workflow.tools]);

    // Memoized handleApplyAll for useEffect dependencies
    const handleApplyAll = useCallback(() => {
        // Find all unapplied action indices
        const unapplied = parsed
            .map((part, idx) => ({ part, actionIndex: idx }))
            .filter(({ part, actionIndex }) => part.type === 'action' && !appliedActions.has(actionIndex))
            .map(({ part, actionIndex }) => ({ 
                action: part.type === 'action' ? part.action : null, 
                actionIndex 
            }))
            .filter(({ action }) => action !== null);

        // Synchronously apply all unapplied actions
        unapplied.forEach(({ action, actionIndex }) => {
            applyAction(action, actionIndex);
        });

        // After all are applied, update the state in one go
        setAppliedActions(prev => {
            const next = new Set(prev);
            unapplied.forEach(({ actionIndex }) => next.add(actionIndex));
            return next;
        });
    }, [parsed, appliedActions, setAppliedActions, applyAction]);

    // Manual single apply (from card)
    const handleSingleApply = (action: any, actionIndex: number) => {
        if (!appliedActions.has(actionIndex)) {
            applyAction(action, actionIndex);
            setAppliedActions(prev => new Set([...prev, actionIndex]));
        }
    };

    useEffect(() => {
        if (loading) {
            // setAutoApplyEnabled(false); // Removed
            setAppliedActions(new Set());
            // setPanelOpen(false); // Removed
        }
    }, [loading]);

    // Removed useEffect for auto-apply

    // Find streaming/ongoing card and extract name
    const streamingPart = parsed.find(part => part.type === 'streaming_action');
    let streamingLine = '';
    if (streamingPart && streamingPart.type === 'streaming_action' && streamingPart.action && streamingPart.action.name) {
        streamingLine = `Generating ${streamingPart.action.name}...`;
    }

    // Only show Apply All button if all cards are loaded (no streaming_action cards) and streaming is finished
    const allCardsLoaded = !loading && actionParts.length > 0 && actionParts.every(part => part.type === 'action');
    // When all cards are loaded, show summary of agents created/updated
    let completedSummary = '';
    if (allCardsLoaded && totalActions > 0) {
        // Count how many are create vs edit
        const createCount = parsed.filter(part => part.type === 'action' && part.action.action === 'create_new').length;
        const editCount = parsed.filter(part => part.type === 'action' && part.action.action === 'edit').length;
        const parts = [];
        if (createCount > 0) parts.push(`${createCount} agent${createCount > 1 ? 's' : ''} created`);
        if (editCount > 0) parts.push(`${editCount} agent${editCount > 1 ? 's' : ''} updated`);
        completedSummary = parts.join(', ');
    }

    // Detect if any card has an error or is cancelled
    const hasPanelWarning = parsed.some(
        part =>
            part.type === 'action' &&
            part.action &&
            (part.action.error || ('cancelled' in part.action && part.action.cancelled))
    );

    // Utility to filter out divider/empty markdown blocks
    function isNonDividerMarkdown(content: string) {
        const trimmed = content.trim();
        return (
            trimmed !== '' &&
            !/^(-{3,}|_{3,}|\*{3,})$/.test(trimmed)
        );
    }

    // At the end of the render, call onStatusBarChange with the current status bar props
    // Track the latest status bar info
    const latestStatusBar = useRef<any>(null);

    // Only call onStatusBarChange if the serializable status actually changes
    const lastStatusRef = useRef<any>(null);
    useEffect(() => {
        if (onStatusBarChange) {
            const status = {
                allCardsLoaded,
                allApplied,
                appliedCount,
                pendingCount,
                streamingLine,
                completedSummary,
                hasPanelWarning,
                // Exclude handleApplyAll from comparison
            };
            if (!lastStatusRef.current || JSON.stringify(lastStatusRef.current) !== JSON.stringify(status)) {
                lastStatusRef.current = status;
                onStatusBarChange({
                    ...status,
                    handleApplyAll, // pass the function, but don't compare it
                });
            }
        }
        // Only depend on the serializable values, not the function
    }, [allCardsLoaded, allApplied, appliedCount, pendingCount, streamingLine, completedSummary, hasPanelWarning, onStatusBarChange, handleApplyAll]);

    // Render all cards inline, not in a panel
    return (
        <div className="w-full">
            <div className="px-4 py-2.5 text-sm leading-relaxed text-gray-700 dark:text-gray-200">
                <div className="flex flex-col gap-2">
                  <PreviewModalProvider>
                    {/* Render markdown and cards inline in order */}
                    {parsed.map((part, idx) => {
                        if (part.type === 'text' && isNonDividerMarkdown(part.content)) {
                            // 原项目实现：过滤掉代码块内的内容（包括 copilot_change 代码块）
                            // 这样可以避免显示原始 JSON 配置，只显示卡片
                            const lines = part.content.split('\n');
                            const filteredLines: string[] = [];
                            let inFence = false;
                            let inCopilotChange = false; // 跟踪是否在 copilot_change 块中（即使没有 ```）
                            
                            for (let i = 0; i < lines.length; i++) {
                                const line = lines[i];
                                const trimmed = line.trim();
                                
                                // 检测代码块开始/结束
                                if (/^\s*```/.test(trimmed)) {
                                    // 如果是 copilot_change 代码块，完全跳过
                                    if (trimmed.includes('copilot_change')) {
                                        inFence = true;
                                        inCopilotChange = true;
                                        continue;
                                    }
                                    inFence = !inFence;
                                    if (!inFence) {
                                        inCopilotChange = false;
                                    }
                                    continue;
                                }
                                
                                // 检测 copilot_change 元数据模式（即使没有 ``` 标记）
                                // 这处理流式输出时未闭合的代码块
                                if (!inFence && !inCopilotChange) {
                                    // 检查是否开始了一个新的 copilot_change 块
                                    if (trimmed.startsWith('// action:') || 
                                        (trimmed.startsWith('// config_type:') && i > 0 && lines[i-1]?.trim().startsWith('// action:')) ||
                                        (trimmed.startsWith('// name:') && i > 1 && 
                                         lines[i-1]?.trim().startsWith('// config_type:') && 
                                         lines[i-2]?.trim().startsWith('// action:'))) {
                                        inCopilotChange = true;
                                        continue;
                                    }
                                }
                                
                                // 如果在代码块内或 copilot_change 块内，跳过
                                if (inFence || inCopilotChange) {
                                    // 检查是否到达 JSON 结束（对于未闭合的代码块）
                                    if (inCopilotChange && !inFence) {
                                        // 检查是否到达 JSON 对象的结束
                                        const braceCount = (line.match(/\{/g) || []).length - (line.match(/\}/g) || []).length;
                                        if (braceCount < 0 && trimmed.includes('}')) {
                                            // 可能到达了 JSON 结束，但需要更精确的检测
                                            // 简单检查：如果这行包含 } 且之前有 {，可能是结束
                                            const hasOpenBrace = lines.slice(0, i).some(l => l.includes('{'));
                                            if (hasOpenBrace) {
                                                inCopilotChange = false;
                                            }
                                        }
                                    }
                                    continue;
                                }
                                
                                // 过滤掉元数据注释行（即使不在代码块内）
                                if (trimmed.startsWith('// action:') || 
                                    trimmed.startsWith('// config_type:') || 
                                    trimmed.startsWith('// name:') ||
                                    trimmed.includes('copilot_change')) {
                                    continue;
                                }
                                
                                filteredLines.push(line);
                            }
                            
                            const filteredContent = filteredLines.join('\n').trim();
                            
                            if (!filteredContent) {
                                return null;
                            }
                            
                            return <MarkdownContent key={`text-${idx}`} content={filteredContent} atValues={atValues} />;
                        }
                        if (part.type === 'action') {
                            return (
                                <Action
                                    key={`action-${idx}`}
                                    msgIndex={messageIndex}
                                    actionIndex={idx}
                                    action={part.action}
                                    workflow={workflow}
                                    dispatch={dispatch}
                                    stale={false}
                                    onApplied={() => handleSingleApply(part.action, idx)}
                                    externallyApplied={appliedActions.has(idx)}
                                    defaultExpanded={true}
                                />
                            );
                        }
                        if (part.type === 'streaming_action') {
                            return (
                                <StreamingAction
                                    key={`streaming-${idx}`}
                                    action={part.action}
                                    loading={loading}
                                />
                            );
                        }
                        return null;
                    })}
                  </PreviewModalProvider>
                </div>
            </div>
        </div>
    );
}

function AssistantMessageLoading({ currentStatus }: { currentStatus: 'thinking' | 'planning' | 'generating' }) {
    const statusText = {
        thinking: "Thinking...",
        planning: "Planning...",
        generating: "Generating..."
    };

    return (
        <div className="w-full">
            <div className="bg-gray-50 dark:bg-gray-800 px-4 py-2.5 
                rounded-lg
                border border-gray-200 dark:border-gray-700
                shadow-sm dark:shadow-gray-950/20 animate-pulse min-h-[2.5rem] flex items-center gap-2">
                <Spinner size="sm" className="ml-2" />
                <span className="text-sm text-gray-600 dark:text-gray-400">{statusText[currentStatus]}</span>
            </div>
        </div>
    );
}

export function Messages({
    messages,
    streamingResponse,
    loadingResponse,
    workflow,
    dispatch,
    onStatusBarChange,
    toolCalling,
    toolQuery,
    toolResult
}: {
    messages: z.infer<typeof CopilotMessage>[];
    streamingResponse: string;
    loadingResponse: boolean;
    workflow: z.infer<typeof Workflow>;
    dispatch: (action: any) => void;
    onStatusBarChange?: (status: any) => void;
    toolCalling?: boolean;
    toolQuery?: string | null;
    toolResult?: string | null;
}) {
    const messagesEndRef = useRef<HTMLDivElement>(null);
    // Combine messages with streaming response if available
    // Avoid duplicate by checking if last message is already assistant message
    const displayMessages = useMemo(() => {
        if (loadingResponse && streamingResponse) {
            // Check if last message is already an assistant message
            const lastMessage = messages[messages.length - 1];
            if (lastMessage?.role === 'assistant') {
                // 如果最后一条消息是助手消息，检查内容是否匹配
                // 如果内容相同或streamingResponse是lastMessage.content的子串，不重复添加
                if (lastMessage.content === streamingResponse || 
                    streamingResponse.startsWith(lastMessage.content)) {
                    // 更新最后一条消息的内容为最新的streamingResponse
                    return [
                        ...messages.slice(0, -1),
                        {
                            ...lastMessage,
                            content: streamingResponse
                        }
                    ];
                }
            }
            // Add streaming response as assistant message
            return [...messages, {
                role: 'assistant' as const,
                content: streamingResponse
            }];
        }
        return messages;
    }, [messages, loadingResponse, streamingResponse]);

    useEffect(() => {
        // Small delay to ensure content is rendered
        const timeoutId = setTimeout(() => {
            messagesEndRef.current?.scrollIntoView({
                behavior: "smooth",
                block: "end",
                inline: "nearest"
            });
        }, 100);

        return () => clearTimeout(timeoutId);
    }, [messages, loadingResponse]);

    // Track the latest status bar info
    const latestStatusBar = useRef<any>(null);

    const renderMessage = (message: z.infer<typeof CopilotMessage>, messageIndex: number) => {
        if (message.role === 'assistant') {
            return (
                <AssistantMessage
                    key={messageIndex}
                    content={message.content}
                    workflow={workflow}
                    dispatch={dispatch}
                    messageIndex={messageIndex}
                    loading={loadingResponse}
                    onStatusBarChange={status => {
                        // Only update for the last assistant message
                        if (messageIndex === displayMessages.length - 1) {
                            latestStatusBar.current = status;
                            onStatusBarChange?.(status);
                        }
                    }}
                />
            );
        }

        if (message.role === 'user' && typeof message.content === 'string') {
            return <UserMessage key={messageIndex} content={message.content} />;
        }

        return null;
    };

    return (
        <div className={displayMessages.length === 0 ? "" : "h-full"}>
            <div className="flex flex-col mb-4">
                {displayMessages.map((message, index) => (
                    <div key={index} className="mb-4">
                        {renderMessage(message, index)}
                    </div>
                ))}
                {!streamingResponse && (toolCalling ? (
                    <div className="text-sm text-gray-600 dark:text-gray-400 mb-2 px-4">
                        <span className="animate-pulse [animation-duration:2s]">Searching for tools{toolQuery ? ` to ${toolQuery}` : ''}...</span>
                    </div>
                ) : loadingResponse ? (
                    <div className="text-sm text-gray-600 dark:text-gray-400 mb-2 px-4">
                        <span className="animate-pulse [animation-duration:2s]">Thinking...</span>
                    </div>
                ) : null)}
            </div>
            <div ref={messagesEndRef} />
        </div>
    );
}