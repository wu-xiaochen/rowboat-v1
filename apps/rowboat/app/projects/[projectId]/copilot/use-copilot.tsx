import { useCallback, useRef, useState } from "react";
import { getCopilotResponseStream } from "@/app/actions/copilot.actions";
import { CopilotMessage } from "@/src/entities/models/copilot";
import { Workflow } from "@/app/lib/types/workflow_types";
import { DataSource } from "@/src/entities/models/data-source";
import { z } from "zod";
import { WithStringId } from "@/app/lib/types/types";

interface UseCopilotParams {
    projectId: string;
    workflow: z.infer<typeof Workflow>;
    context: any;
    dataSources?: z.infer<typeof DataSource>[];
}

interface UseCopilotResult {
    streamingResponse: string;
    loading: boolean;
    toolCalling: boolean;
    toolQuery: string | null;
    toolResult: string | null;
    error: string | null;
    clearError: () => void;
    billingError: string | null;
    clearBillingError: () => void;
    start: (
        messages: z.infer<typeof CopilotMessage>[],
        onDone: (finalResponse: string) => void,
    ) => void;
    cancel: () => void;
}

export function useCopilot({ projectId, workflow, context, dataSources }: UseCopilotParams): UseCopilotResult {
    const [streamingResponse, setStreamingResponse] = useState('');
    const [loading, setLoading] = useState(false);
    const [toolCalling, setToolCalling] = useState(false);
    const [toolQuery, setToolQuery] = useState<string | null>(null);
    const [toolResult, setToolResult] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [billingError, setBillingError] = useState<string | null>(null);
    const cancelRef = useRef<() => void>(() => { });
    const responseRef = useRef('');
    const inFlightRef = useRef(false);

    function clearError() {
        setError(null);
    }

    function clearBillingError() {
        setBillingError(null);
    }

    const start = useCallback(async (
        messages: z.infer<typeof CopilotMessage>[],
        onDone: (finalResponse: string) => void,
    ) => {
        

        if (!messages.length || messages.at(-1)?.role !== 'user') {
            
            return;
        }

        // Prevent duplicate/concurrent starts (e.g., StrictMode double effects or remounts)
        if (inFlightRef.current) {
            
            return;
        }
        inFlightRef.current = true;

        setStreamingResponse('');
        responseRef.current = '';
        setError(null);
        setToolCalling(false);
        setToolQuery(null);
        setToolResult(null);
        setLoading(true);

        try {
            // Wait 2 rAF frames to let layout stabilize (avoids StrictMode/remount race on initial load)
            await new Promise<void>((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve())));
            
            // 验证权限（异步，但不阻塞）
            getCopilotResponseStream(projectId, messages, workflow, context || null, dataSources).catch(err => {
                const errorMessage = err?.message || String(err || 'Unknown error');
                if (errorMessage.includes('billing') || errorMessage.includes('credits')) {
                    setBillingError(errorMessage);
                    setError(errorMessage);
                    setLoading(false);
                    inFlightRef.current = false;
                }
            });

            // 直接连接到后端API（通过前端代理）
            const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';
            const requestBody = {
                projectId,
                messages,
                workflow,
                context: context || undefined,
                dataSources: dataSources || undefined,
            };
            
            // 使用fetch进行流式请求，因为EventSource不支持POST
            console.log('🚀 Sending Copilot request to:', `/api/v1/${projectId}/copilot/stream`);
            console.log('📤 Request body:', JSON.stringify(requestBody, null, 2));
            
            const response = await fetch(`/api/v1/${projectId}/copilot/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody),
            });
            
            console.log('📥 Response status:', response.status, response.statusText);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
                // 确保错误信息是字符串，而不是对象
                let errorMessage = 'Failed to start stream';
                if (errorData) {
                    if (typeof errorData === 'string') {
                        errorMessage = errorData;
                    } else if (errorData.error) {
                        errorMessage = typeof errorData.error === 'string' ? errorData.error : JSON.stringify(errorData.error);
                    } else if (errorData.message) {
                        errorMessage = typeof errorData.message === 'string' ? errorData.message : JSON.stringify(errorData.message);
                    } else {
                        errorMessage = JSON.stringify(errorData);
                    }
                }
                setError(errorMessage);
                setLoading(false);
                inFlightRef.current = false;
                return;
            }
            
            // 使用ReadableStream处理SSE
            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            
            if (!reader) {
                setError('Failed to get stream reader');
                setLoading(false);
                inFlightRef.current = false;
                return;
            }

            let buffer = '';
            let pendingUpdate = false;
            let updateTimer: NodeJS.Timeout | null = null;
            
            // 批量更新流式响应的辅助函数
            const scheduleUpdate = () => {
                if (!pendingUpdate) {
                    pendingUpdate = true;
                    // 使用 requestAnimationFrame 批量更新，避免频繁渲染
                    updateTimer = setTimeout(() => {
                        setStreamingResponse(responseRef.current);
                        pendingUpdate = false;
                        updateTimer = null;
                    }, 16); // 约 60fps
                }
            };
            
            // 处理流式数据
            const processStream = async () => {
                try {
                    while (true) {
                        const { done, value } = await reader.read();
                        
                        if (done) {
                            // 流结束，立即更新最后一次
                            if (updateTimer) {
                                clearTimeout(updateTimer);
                                updateTimer = null;
                            }
                            setStreamingResponse(responseRef.current);
                            break;
                        }
                        
                        buffer += decoder.decode(value, { stream: true });
                        const lines = buffer.split('\n');
                        buffer = lines.pop() || ''; // 保留最后一个不完整的行
                        
                        let currentEventType = 'message'; // 默认事件类型
                        
                        for (const line of lines) {
                            if (line.startsWith('event: ')) {
                                currentEventType = line.substring(7).trim();
                            } else if (line.startsWith('data: ')) {
                                const dataStr = line.substring(6).trim();
                                if (dataStr) {
                try {
                                        const data = JSON.parse(dataStr);
                                        
                                        if (currentEventType === 'message') {
                    if (data.content) {
                        // 先更新 ref，然后批量更新 state
                        responseRef.current += data.content;
                        scheduleUpdate(); // 使用批量更新，避免频繁渲染
                                            }
                                        } else if (currentEventType === 'tool-call') {
                                            console.log('🔧 Tool call event:', data);
                                            setToolCalling(true);
                                            setToolQuery(data.query || data.args?.query || null);
                                        } else if (currentEventType === 'tool-result') {
                                            console.log('✅ Tool result event:', data);
                                            setToolCalling(false);
                                            // 存储工具结果（截断过长内容）
                                            if (data.result) {
                                                const resultStr = typeof data.result === 'string' ? data.result : JSON.stringify(data.result);
                                                // 限制显示长度，避免过长
                                                const maxLength = 500;
                                                setToolResult(resultStr.length > maxLength ? resultStr.substring(0, maxLength) + '...' : resultStr);
                                            }
                                        } else if (currentEventType === 'action-start') {
                                            console.log('🎯 Action start event:', data);
                                            // action-start事件表示检测到copilot_change元数据
                                            // 前端解析逻辑会自动处理，这里不需要特殊处理
                                        } else if (currentEventType === 'done') {
                                            // done事件，流结束
                                            break;
                                        } else if (currentEventType === 'error') {
                                            // 确保错误信息是字符串，而不是对象
                                            let errorMessage = 'Stream error';
                                            if (data) {
                                                if (typeof data === 'string') {
                                                    errorMessage = data;
                                                } else if (data.error) {
                                                    errorMessage = typeof data.error === 'string' ? data.error : JSON.stringify(data.error);
                                                } else if (data.content) {
                                                    errorMessage = typeof data.content === 'string' ? data.content : JSON.stringify(data.content);
                                                } else if (data.message) {
                                                    errorMessage = typeof data.message === 'string' ? data.message : JSON.stringify(data.message);
                                                } else {
                                                    errorMessage = JSON.stringify(data);
                                                }
                                            }
                                            console.error('❌ Stream error:', errorMessage);
                                            // 清理定时器
                                            if (updateTimer) {
                                                clearTimeout(updateTimer);
                                                updateTimer = null;
                                            }
                                            setError(errorMessage);
                                            setLoading(false);
                                            inFlightRef.current = false;
                                            return;
                    }
                } catch (e) {
                                        console.error('❌ Failed to parse stream data:', e, dataStr);
                } finally {
                                        // 确保在错误时状态已更新
                                        if (updateTimer && currentEventType === 'error') {
                                            clearTimeout(updateTimer);
                                            updateTimer = null;
                                            setStreamingResponse(responseRef.current);
                                        }
                }
                                }
                            } else if (line.trim() === '') {
                                // 空行表示事件结束，重置事件类型
                                currentEventType = 'message';
                            }
                }
                    }
                    
                    // 流结束
                setLoading(false);
                // 确保所有待更新的状态都已更新
                if (updateTimer) {
                    clearTimeout(updateTimer);
                    updateTimer = null;
                }
                setStreamingResponse(responseRef.current);
                const finalResponse = responseRef.current || '';
                if (finalResponse) {
                    console.log('📝 Final response:', { 
                        length: finalResponse.length, 
                        preview: finalResponse.substring(0, 100) 
                    });
                } else {
                    console.warn('⚠️ Final response is empty');
                }
                onDone(finalResponse);
                inFlightRef.current = false;
                } catch (error) {
                    console.error('❌ Error processing stream:', error);
                    // 清理定时器
                    if (updateTimer) {
                        clearTimeout(updateTimer);
                        updateTimer = null;
                    }
                    setError('Stream processing failed');
                    setLoading(false);
                    inFlightRef.current = false;
                } finally {
                    // 确保最终状态已更新
                    if (updateTimer) {
                        clearTimeout(updateTimer);
                        updateTimer = null;
                    }
                    setStreamingResponse(responseRef.current);
                }
            };
            
            // 启动流处理
            processStream();
            
            // 设置取消函数
            cancelRef.current = () => {
                reader.cancel();
                    setLoading(false);
                inFlightRef.current = false;
            };

            // 旧的EventSource代码已移除，现在使用fetch + ReadableStream
        } catch (err) {
            console.error('❌ Error in useCopilot.start:', err);
            setError('Failed to initiate stream');
            setLoading(false);
            inFlightRef.current = false;
        }
    }, [projectId, workflow, context, dataSources]);

    const cancel = useCallback(() => {
        cancelRef.current?.();
        setLoading(false);
        inFlightRef.current = false;
    }, []);

    return {
        streamingResponse,
        loading,
        toolCalling,
        toolQuery,
        toolResult,
        error,
        clearError,
        billingError,
        clearBillingError,
        start,
        cancel,
    };
}
