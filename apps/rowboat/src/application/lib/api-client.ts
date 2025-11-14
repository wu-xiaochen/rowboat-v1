/**
 * 统一API客户端
 * Unified API client for backend communication
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';

/**
 * API响应格式
 */
export interface ApiResponse<T = any> {
    success: boolean;
    data?: T;
    error?: {
        code: string;
        message: string;
        details?: any;
    };
    message?: string;
}

/**
 * API请求配置
 */
export interface ApiRequestConfig extends RequestInit {
    apiKey?: string;
}

/**
 * API客户端类
 */
export class ApiClient {
    private baseUrl: string;

    constructor(baseUrl: string = API_BASE_URL) {
        this.baseUrl = baseUrl.replace(/\/$/, ''); // 移除尾部斜杠
    }

    /**
     * 发送HTTP请求
     */
    private async request<T>(
        endpoint: string,
        config: ApiRequestConfig = {}
    ): Promise<ApiResponse<T>> {
        const { apiKey, ...fetchConfig } = config;

        // 构建URL
        const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

        // 构建请求头
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            ...(fetchConfig.headers as Record<string, string> || {}),
        };

        // 添加API Key（如果提供）
        if (apiKey) {
            headers['Authorization'] = `Bearer ${apiKey}`;
        }

        try {
            const response = await fetch(url, {
                ...fetchConfig,
                headers,
            });

            // 处理流式响应
            if (response.headers.get('content-type')?.includes('text/event-stream')) {
                // 返回流式响应
                return response as any;
            }

            // 解析JSON响应
            const data = await response.json();

            if (!response.ok) {
                return {
                    success: false,
                    error: {
                        code: data.error?.code || 'HTTP_ERROR',
                        message: data.error?.message || data.message || `HTTP ${response.status}: ${response.statusText}`,
                        details: data.error?.details,
                    },
                };
            }

            return {
                success: true,
                data: data.data || data,
                message: data.message,
            };
        } catch (error) {
            return {
                success: false,
                error: {
                    code: 'NETWORK_ERROR',
                    message: error instanceof Error ? error.message : 'Network error occurred',
                },
            };
        }
    }

    /**
     * GET请求
     */
    async get<T>(endpoint: string, config: ApiRequestConfig = {}): Promise<ApiResponse<T>> {
        return this.request<T>(endpoint, {
            ...config,
            method: 'GET',
        });
    }

    /**
     * POST请求
     */
    async post<T>(
        endpoint: string,
        body?: any,
        config: ApiRequestConfig = {}
    ): Promise<ApiResponse<T>> {
        return this.request<T>(endpoint, {
            ...config,
            method: 'POST',
            body: body ? JSON.stringify(body) : undefined,
        });
    }

    /**
     * PUT请求
     */
    async put<T>(
        endpoint: string,
        body?: any,
        config: ApiRequestConfig = {}
    ): Promise<ApiResponse<T>> {
        return this.request<T>(endpoint, {
            ...config,
            method: 'PUT',
            body: body ? JSON.stringify(body) : undefined,
        });
    }

    /**
     * DELETE请求
     */
    async delete<T>(endpoint: string, config: ApiRequestConfig = {}): Promise<ApiResponse<T>> {
        return this.request<T>(endpoint, {
            ...config,
            method: 'DELETE',
        });
    }

    /**
     * 流式请求（SSE）
     */
    async stream(
        endpoint: string,
        body?: any,
        config: ApiRequestConfig = {}
    ): Promise<ReadableStream<Uint8Array> | null> {
        const { apiKey, ...fetchConfig } = config;

        // 构建URL
        const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

        // 构建请求头
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            ...(fetchConfig.headers as Record<string, string> || {}),
        };

        // 添加API Key（如果提供）
        if (apiKey) {
            headers['Authorization'] = `Bearer ${apiKey}`;
        }

        try {
            const response = await fetch(url, {
                ...fetchConfig,
                method: 'POST',
                headers,
                body: body ? JSON.stringify(body) : undefined,
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // 返回流式响应
            return response.body;
        } catch (error) {
            console.error('Stream request error:', error);
            return null;
        }
    }
}

// 导出默认API客户端实例
export const apiClient = new ApiClient();

// 导出API客户端工厂函数
export function createApiClient(baseUrl?: string): ApiClient {
    return new ApiClient(baseUrl);
}

