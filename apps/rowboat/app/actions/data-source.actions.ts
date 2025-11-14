'use server';
import { z } from 'zod';
import { DataSourceDoc } from "@/src/entities/models/data-source-doc";
import { DataSource } from "@/src/entities/models/data-source";
import { container } from "@/di/container";
import { IFetchDataSourceController } from "@/src/interface-adapters/controllers/data-sources/fetch-data-source.controller";
import { authCheck } from "./auth.actions";
import { IListDataSourcesController } from "@/src/interface-adapters/controllers/data-sources/list-data-sources.controller";
import { ICreateDataSourceController } from "@/src/interface-adapters/controllers/data-sources/create-data-source.controller";
import { IRecrawlWebDataSourceController } from "@/src/interface-adapters/controllers/data-sources/recrawl-web-data-source.controller";
import { IDeleteDataSourceController } from "@/src/interface-adapters/controllers/data-sources/delete-data-source.controller";
import { IToggleDataSourceController } from "@/src/interface-adapters/controllers/data-sources/toggle-data-source.controller";
import { IAddDocsToDataSourceController } from "@/src/interface-adapters/controllers/data-sources/add-docs-to-data-source.controller";
import { IListDocsInDataSourceController } from "@/src/interface-adapters/controllers/data-sources/list-docs-in-data-source.controller";
import { IDeleteDocFromDataSourceController } from "@/src/interface-adapters/controllers/data-sources/delete-doc-from-data-source.controller";
import { IGetDownloadUrlForFileController } from "@/src/interface-adapters/controllers/data-sources/get-download-url-for-file.controller";
import { IGetUploadUrlsForFilesController } from "@/src/interface-adapters/controllers/data-sources/get-upload-urls-for-files.controller";
import { IUpdateDataSourceController } from "@/src/interface-adapters/controllers/data-sources/update-data-source.controller";
import { dataSourcesApiClient } from "@/src/application/lib/backend-api-client";

// ⚠️ 已弃用：旧的TypeScript实现，将逐步迁移到Python后端API
// ⚠️ DEPRECATED: Old TypeScript implementation, migrating to Python backend API
const fetchDataSourceController = container.resolve<IFetchDataSourceController>("fetchDataSourceController");
const listDataSourcesController = container.resolve<IListDataSourcesController>("listDataSourcesController");
const createDataSourceController = container.resolve<ICreateDataSourceController>("createDataSourceController");
const recrawlWebDataSourceController = container.resolve<IRecrawlWebDataSourceController>("recrawlWebDataSourceController");
const deleteDataSourceController = container.resolve<IDeleteDataSourceController>("deleteDataSourceController");
const toggleDataSourceController = container.resolve<IToggleDataSourceController>("toggleDataSourceController");
const addDocsToDataSourceController = container.resolve<IAddDocsToDataSourceController>("addDocsToDataSourceController");
const listDocsInDataSourceController = container.resolve<IListDocsInDataSourceController>("listDocsInDataSourceController");
const deleteDocFromDataSourceController = container.resolve<IDeleteDocFromDataSourceController>("deleteDocFromDataSourceController");
const getDownloadUrlForFileController = container.resolve<IGetDownloadUrlForFileController>("getDownloadUrlForFileController");
const getUploadUrlsForFilesController = container.resolve<IGetUploadUrlsForFilesController>("getUploadUrlsForFilesController");
const updateDataSourceController = container.resolve<IUpdateDataSourceController>("updateDataSourceController");

/**
 * 获取数据源详情
 * 已迁移到Python后端API
 * 
 * @param sourceId - 数据源ID
 * @param projectId - 项目ID（可选，如果有则使用后端API，否则使用旧实现）
 */
export async function getDataSource(
    sourceId: string,
    projectId?: string
): Promise<z.infer<typeof DataSource>> {
    const user = await authCheck();
    
    // 如果有projectId，使用后端API
    if (projectId) {
        const response = await dataSourcesApiClient.get(projectId, sourceId);
        if (!response.success || !response.data) {
            throw new Error(response.error?.message || '获取数据源失败');
        }
        // 验证返回的数据格式
        return DataSource.parse(response.data);
    }
    
    // 否则使用旧实现（向后兼容）
    return await fetchDataSourceController.execute({
        caller: 'user',
        userId: user.id,
        sourceId,
    });
}

/**
 * 获取数据源列表
 * 已迁移到Python后端API
 */
export async function listDataSources(projectId: string): Promise<z.infer<typeof DataSource>[]> {
    const user = await authCheck();

    // 使用后端API
    const response = await dataSourcesApiClient.list(projectId);
    if (!response.success || !response.data) {
        throw new Error(response.error?.message || '获取数据源列表失败');
    }
    
    // 验证返回的数据格式（数组）
    if (!Array.isArray(response.data)) {
        throw new Error('数据源列表格式错误');
    }
    
    // 验证每个数据源
    return response.data.map(item => DataSource.parse(item));
}

/**
 * 创建数据源
 * 已迁移到Python后端API
 */
export async function createDataSource({
    projectId,
    name,
    description,
    data,
    status = 'pending',
}: {
    projectId: string,
    name: string,
    description?: string,
    data: z.infer<typeof DataSource>['data'],
    status?: 'pending' | 'ready',
}): Promise<z.infer<typeof DataSource>> {
    const user = await authCheck();
    
    // 使用后端API
    const response = await dataSourcesApiClient.create(projectId, {
        name,
        description: description || '',
        data: data as { type: string },
        status,
    });
    
    if (!response.success || !response.data) {
        throw new Error(response.error?.message || '创建数据源失败');
    }
    
    // 验证返回的数据格式
    return DataSource.parse(response.data);
}

export async function recrawlWebDataSource(sourceId: string) {
    const user = await authCheck();

    return await recrawlWebDataSourceController.execute({
        caller: 'user',
        userId: user.id,
        sourceId,
    });
}

/**
 * 删除数据源
 * 已迁移到Python后端API
 * 
 * @param sourceId - 数据源ID
 * @param projectId - 项目ID（可选，如果有则使用后端API，否则使用旧实现）
 */
export async function deleteDataSource(sourceId: string, projectId?: string) {
    const user = await authCheck();

    // 如果有projectId，使用后端API
    if (projectId) {
        const response = await dataSourcesApiClient.delete(projectId, sourceId);
        if (!response.success) {
            throw new Error(response.error?.message || '删除数据源失败');
        }
        return;
    }
    
    // 否则使用旧实现（向后兼容）
    return await deleteDataSourceController.execute({
        caller: 'user',
        userId: user.id,
        sourceId,
    });
}

/**
 * 切换数据源状态
 * 已迁移到Python后端API
 * 
 * @param sourceId - 数据源ID
 * @param active - 是否激活
 * @param projectId - 项目ID（可选，如果有则使用后端API，否则使用旧实现）
 */
export async function toggleDataSource(
    sourceId: string,
    active: boolean,
    projectId?: string
) {
    const user = await authCheck();

    // 如果有projectId，使用后端API
    if (projectId) {
        const response = await dataSourcesApiClient.toggle(projectId, sourceId, { active });
        if (!response.success || !response.data) {
            throw new Error(response.error?.message || '切换数据源状态失败');
        }
        return DataSource.parse(response.data);
    }
    
    // 否则使用旧实现（向后兼容）
    return await toggleDataSourceController.execute({
        caller: 'user',
        userId: user.id,
        sourceId,
        active,
    });
}

export async function addDocsToDataSource({
    sourceId,
    docData,
}: {
    sourceId: string,
    docData: {
        name: string,
        data: z.infer<typeof DataSourceDoc>['data']
    }[]
}): Promise<void> {
    const user = await authCheck();

    return await addDocsToDataSourceController.execute({
        caller: 'user',
        userId: user.id,
        sourceId,
        docs: docData,
    });
}

export async function listDocsInDataSource({
    sourceId,
    page = 1,
    limit = 10,
}: {
    sourceId: string,
    page?: number,
    limit?: number,
}): Promise<{
    files: z.infer<typeof DataSourceDoc>[],
    total: number
}> {
    const user = await authCheck();

    const docs = await listDocsInDataSourceController.execute({
        caller: 'user',
        userId: user.id,
        sourceId,
    });

    return {
        files: docs,
        total: docs.length,
    };
}

export async function deleteDocFromDataSource({
    docId,
}: {
    docId: string,
}): Promise<void> {
    const user = await authCheck();
    return await deleteDocFromDataSourceController.execute({
        caller: 'user',
        userId: user.id,
        docId,
    });
}

export async function getDownloadUrlForFile(
    fileId: string
): Promise<string> {
    const user = await authCheck();

    return await getDownloadUrlForFileController.execute({
        caller: 'user',
        userId: user.id,
        fileId,
    });
}

export async function getUploadUrlsForFilesDataSource(
    sourceId: string,
    files: { name: string; type: string; size: number }[]
): Promise<{
    fileId: string,
    uploadUrl: string,
    path: string,
}[]> {
    const user = await authCheck();

    return await getUploadUrlsForFilesController.execute({
        caller: 'user',
        userId: user.id,
        sourceId,
        files,
    });
}

/**
 * 更新数据源
 * 已迁移到Python后端API
 * 
 * @param sourceId - 数据源ID
 * @param description - 描述
 * @param projectId - 项目ID（可选，如果有则使用后端API，否则使用旧实现）
 */
export async function updateDataSource({
    sourceId,
    description,
    projectId,
}: {
    sourceId: string,
    description: string,
    projectId?: string,
}) {
    const user = await authCheck();

    // 如果有projectId，使用后端API
    if (projectId) {
        const response = await dataSourcesApiClient.update(projectId, sourceId, { description });
        if (!response.success || !response.data) {
            throw new Error(response.error?.message || '更新数据源失败');
        }
        return DataSource.parse(response.data);
    }
    
    // 否则使用旧实现（向后兼容）
    return await updateDataSourceController.execute({
        caller: 'user',
        userId: user.id,
        sourceId,
        data: {
            description,
        },
    });
}
