/**
 * 聊天API客户端
 * Chat API client for backend communication
 */

import { apiClient, ApiClient } from './api-client';
import { Message } from '@/app/lib/types/types';

/**
 * 聊天请求
 */
export interface ChatRequest {
    conversationId?: string;
    messages: Message[];
    mockTools?: Record<string, string>;
    stream?: boolean;
}

/**
 * 聊天响应
 */
export interface ChatResponse {
    conversationId: string;
    turn: {
        id: string;
        reason: {
            type: 'api' | 'chat' | 'job';
        };
        input: {
            messages: Message[];
            mockTools?: Record<string, string>;
        };
        output: Message[];
        error?: string | null;
        isBillingError: boolean;
        createdAt: string;
        updatedAt?: string | null;
    };
}

/**
 * Turn事件
 */
export interface TurnEvent {
    type: 'message' | 'done' | 'error';
    data?: Message;
    conversationId?: string;
    turn?: ChatResponse['turn'];
    error?: string;
    isBillingError?: boolean;
}

/**
 * 聊天API客户端类
 */
export class ChatApiClient {
    private apiClient: ApiClient;

    constructor(apiClient: ApiClient = apiClient) {
        this.apiClient = apiClient;
    }

    /**
     * 发送聊天消息（非流式）
     */
    async sendMessage(
        projectId: string,
        request: ChatRequest,
        apiKey?: string
    ): Promise<ChatResponse> {
        const response = await this.apiClient.post<ChatResponse>(
            `/api/v1/${projectId}/chat`,
            {
                ...request,
                stream: false,
            },
            {
                apiKey,
            }
        );

        if (!response.success || !response.data) {
            throw new Error(response.error?.message || 'Chat request failed');
        }

        return response.data;
    }

    /**
     * 发送聊天消息（流式）
     */
    async* sendMessageStream(
        projectId: string,
        request: ChatRequest,
        apiKey?: string
    ): AsyncGenerator<TurnEvent, void, unknown> {
        const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';
        const url = `${API_BASE_URL}/api/v1/${projectId}/chat`;

        // 构建请求头
        const headers: HeadersInit = {
            'Content-Type': 'application/json',
        };

        // 添加API Key（如果提供）
        if (apiKey) {
            headers['Authorization'] = `Bearer ${apiKey}`;
        }

        // 发送请求
        const response = await fetch(url, {
            method: 'POST',
            headers,
            body: JSON.stringify({
                ...request,
                stream: true,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        // 解析SSE流
        const reader = response.body?.getReader();
        if (!reader) {
            throw new Error('No response body');
        }

        const decoder = new TextDecoder();
        let buffer = '';

        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    break;
                }

                // 解码数据
                buffer += decoder.decode(value, { stream: true });

                // 处理SSE事件
                // SSE格式: event: {type}\ndata: {json}\n\n
                const parts = buffer.split('\n\n');
                buffer = parts.pop() || ''; // 保留最后不完整的事件

                for (const part of parts) {
                    if (!part.trim()) continue;

                    let eventType = 'message';
                    let eventData: string | null = null;

                    const lines = part.split('\n');
                    for (const line of lines) {
                        if (line.startsWith('event: ')) {
                            eventType = line.substring(7).trim();
                        } else if (line.startsWith('data: ')) {
                            const dataLine = line.substring(6).trim();
                            if (eventData) {
                                // 如果有多行data，合并它们
                                eventData += '\n' + dataLine;
                            } else {
                                eventData = dataLine;
                            }
                        }
                    }

                    // 处理事件数据
                    if (eventData) {
                        try {
                            const data = JSON.parse(eventData);
                            // 确保事件类型正确
                            if (!data.type) {
                                data.type = eventType;
                            }
                            yield data as TurnEvent;
                        } catch (e) {
                            console.error('Failed to parse SSE event:', e, eventData);
                        }
                    }
                }
            }

            // 处理缓冲区中剩余的数据
            if (buffer.trim()) {
                const parts = buffer.split('\n\n');
                for (const part of parts) {
                    if (!part.trim()) continue;

                    let eventType = 'message';
                    let eventData: string | null = null;

                    const lines = part.split('\n');
                    for (const line of lines) {
                        if (line.startsWith('event: ')) {
                            eventType = line.substring(7).trim();
                        } else if (line.startsWith('data: ')) {
                            const dataLine = line.substring(6).trim();
                            if (eventData) {
                                eventData += '\n' + dataLine;
                            } else {
                                eventData = dataLine;
                            }
                        }
                    }

                    if (eventData) {
                        try {
                            const data = JSON.parse(eventData);
                            if (!data.type) {
                                data.type = eventType;
                            }
                            yield data as TurnEvent;
                        } catch (e) {
                            console.error('Failed to parse SSE event:', e, eventData);
                        }
                    }
                }
            }
        } finally {
            reader.releaseLock();
        }
    }
}

// 导出默认聊天API客户端实例
export const chatApiClient = new ChatApiClient();

// 导出聊天API客户端工厂函数
export function createChatApiClient(apiClient?: ApiClient): ChatApiClient {
    return new ChatApiClient(apiClient);
}

