/**
 * 后端API客户端
 * Backend API client for new Python backend endpoints
 * 
 * 此文件包含所有新实现的后端API端点的客户端方法
 * This file contains client methods for all newly implemented backend API endpoints
 */

import { apiClient, ApiResponse } from './api-client';

/**
 * 数据源API客户端
 */
export class DataSourcesApiClient {
    /**
     * 创建数据源
     */
    async create(
        projectId: string,
        data: {
            name: string;
            description?: string;
            data: { type: string };
            status?: string;
        }
    ): Promise<ApiResponse<any>> {
        return apiClient.post(`/api/v1/${projectId}/data-sources`, data);
    }

    /**
     * 获取数据源列表
     * 注意：后端返回的是数组，不是分页对象
     */
    async list(
        projectId: string,
        params?: {
            active?: boolean;
            deleted?: boolean;
            cursor?: string;
            limit?: number;
        }
    ): Promise<ApiResponse<any[]>> {
        const queryParams = new URLSearchParams();
        if (params?.active !== undefined) queryParams.append('active', params.active.toString());
        if (params?.deleted !== undefined) queryParams.append('deleted', params.deleted.toString());
        if (params?.cursor) queryParams.append('cursor', params.cursor);
        if (params?.limit) queryParams.append('limit', params.limit.toString());
        
        const query = queryParams.toString();
        const response = await apiClient.get(`/api/v1/${projectId}/data-sources${query ? `?${query}` : ''}`);
        // 后端返回的data是数组
        return response;
    }

    /**
     * 获取数据源详情
     */
    async get(projectId: string, sourceId: string): Promise<ApiResponse<any>> {
        return apiClient.get(`/api/v1/${projectId}/data-sources/${sourceId}`);
    }

    /**
     * 更新数据源
     */
    async update(
        projectId: string,
        sourceId: string,
        data: { description?: string }
    ): Promise<ApiResponse<any>> {
        return apiClient.put(`/api/v1/${projectId}/data-sources/${sourceId}`, data);
    }

    /**
     * 删除数据源
     */
    async delete(projectId: string, sourceId: string): Promise<ApiResponse<void>> {
        return apiClient.delete(`/api/v1/${projectId}/data-sources/${sourceId}`);
    }

    /**
     * 切换数据源状态
     */
    async toggle(
        projectId: string,
        sourceId: string,
        data: { active: boolean }
    ): Promise<ApiResponse<any>> {
        return apiClient.post(`/api/v1/${projectId}/data-sources/${sourceId}/toggle`, data);
    }
}

/**
 * 对话API客户端
 */
export class ConversationsApiClient {
    /**
     * 获取对话列表
     */
    async list(
        projectId: string,
        params?: {
            cursor?: string;
            limit?: number;
        }
    ): Promise<ApiResponse<{ items: any[]; nextCursor: string | null }>> {
        const queryParams = new URLSearchParams();
        if (params?.cursor) queryParams.append('cursor', params.cursor);
        if (params?.limit) queryParams.append('limit', params.limit.toString());
        
        const query = queryParams.toString();
        return apiClient.get(`/api/v1/${projectId}/conversations${query ? `?${query}` : ''}`);
    }

    /**
     * 获取对话详情
     */
    async get(projectId: string, conversationId: string): Promise<ApiResponse<any>> {
        return apiClient.get(`/api/v1/${projectId}/conversations/${conversationId}`);
    }
}

/**
 * 任务API客户端
 */
export class JobsApiClient {
    /**
     * 获取任务列表
     */
    async list(
        projectId: string,
        params?: {
            status?: string;
            recurringJobRuleId?: string;
            composioTriggerDeploymentId?: string;
            createdAfter?: string;
            createdBefore?: string;
            cursor?: string;
            limit?: number;
        }
    ): Promise<ApiResponse<{ items: any[]; nextCursor: string | null }>> {
        const queryParams = new URLSearchParams();
        if (params?.status) queryParams.append('status', params.status);
        if (params?.recurringJobRuleId) queryParams.append('recurringJobRuleId', params.recurringJobRuleId);
        if (params?.composioTriggerDeploymentId) queryParams.append('composioTriggerDeploymentId', params.composioTriggerDeploymentId);
        if (params?.createdAfter) queryParams.append('createdAfter', params.createdAfter);
        if (params?.createdBefore) queryParams.append('createdBefore', params.createdBefore);
        if (params?.cursor) queryParams.append('cursor', params.cursor);
        if (params?.limit) queryParams.append('limit', params.limit.toString());
        
        const query = queryParams.toString();
        return apiClient.get(`/api/v1/${projectId}/jobs${query ? `?${query}` : ''}`);
    }

    /**
     * 获取任务详情
     */
    async get(projectId: string, jobId: string): Promise<ApiResponse<any>> {
        return apiClient.get(`/api/v1/${projectId}/jobs/${jobId}`);
    }
}

// 导出默认实例
export const dataSourcesApiClient = new DataSourcesApiClient();
export const conversationsApiClient = new ConversationsApiClient();
export const jobsApiClient = new JobsApiClient();

