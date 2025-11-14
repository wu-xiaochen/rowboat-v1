"use server";

import { container } from "@/di/container";
import { IListJobsController } from "@/src/interface-adapters/controllers/jobs/list-jobs.controller";
import { IFetchJobController } from "@/src/interface-adapters/controllers/jobs/fetch-job.controller";
import { authCheck } from "./auth.actions";
import { JobFiltersSchema } from "@/src/application/repositories/jobs.repository.interface";
import { z } from "zod";
import { jobsApiClient } from "@/src/application/lib/backend-api-client";
import { ListedJobItem } from "@/src/application/repositories/jobs.repository.interface";
import { Job } from "@/src/entities/models/job";

// ⚠️ 已弃用：旧的TypeScript实现，将逐步迁移到Python后端API
// ⚠️ DEPRECATED: Old TypeScript implementation, migrating to Python backend API
const listJobsController = container.resolve<IListJobsController>('listJobsController');
const fetchJobController = container.resolve<IFetchJobController>('fetchJobController');

/**
 * 获取任务列表
 * 已迁移到Python后端API
 */
export async function listJobs(request: {
    projectId: string,
    filters?: z.infer<typeof JobFiltersSchema>,
    cursor?: string,
    limit?: number,
}) {
    const user = await authCheck();

    // 使用后端API
    const response = await jobsApiClient.list(request.projectId, {
        status: request.filters?.status,
        recurringJobRuleId: request.filters?.recurringJobRuleId,
        composioTriggerDeploymentId: request.filters?.composioTriggerDeploymentId,
        createdAfter: request.filters?.createdAfter,
        createdBefore: request.filters?.createdBefore,
        cursor: request.cursor,
        limit: request.limit,
    });
    
    if (!response.success || !response.data) {
        throw new Error(response.error?.message || '获取任务列表失败');
    }
    
    // 验证返回的数据格式
    const { items, nextCursor } = response.data;
    if (!Array.isArray(items)) {
        throw new Error('任务列表格式错误');
    }
    
    // 验证每个任务项
    const validatedItems = items.map(item => ListedJobItem.parse(item));
    
    return {
        items: validatedItems,
        nextCursor: nextCursor,
    };
}

/**
 * 获取任务详情
 * 已迁移到Python后端API
 * 
 * @param jobId - 任务ID
 * @param projectId - 项目ID（可选，如果有则使用后端API，否则使用旧实现）
 */
export async function fetchJob(
    request: {
        jobId: string,
        projectId?: string,
    }
) {
    const user = await authCheck();

    // 如果有projectId，使用后端API
    if (request.projectId) {
        const response = await jobsApiClient.get(request.projectId, request.jobId);
        if (!response.success || !response.data) {
            throw new Error(response.error?.message || '获取任务详情失败');
        }
        // 验证返回的数据格式
        return Job.parse(response.data);
    }
    
    // 否则使用旧实现（向后兼容）
    return await fetchJobController.execute({
        caller: 'user',
        userId: user.id,
        jobId: request.jobId,
    });
}