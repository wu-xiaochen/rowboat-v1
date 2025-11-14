"use server";

import { container } from "@/di/container";
import { IListConversationsController } from "@/src/interface-adapters/controllers/conversations/list-conversations.controller";
import { IFetchConversationController } from "@/src/interface-adapters/controllers/conversations/fetch-conversation.controller";
import { authCheck } from "./auth.actions";
import { conversationsApiClient } from "@/src/application/lib/backend-api-client";
import { ListedConversationItem } from "@/src/application/repositories/conversations.repository.interface";
import { Conversation } from "@/src/entities/models/conversation";
import { z } from "zod";

// ⚠️ 已弃用：旧的TypeScript实现，将逐步迁移到Python后端API
// ⚠️ DEPRECATED: Old TypeScript implementation, migrating to Python backend API
const listConversationsController = container.resolve<IListConversationsController>('listConversationsController');
const fetchConversationController = container.resolve<IFetchConversationController>('fetchConversationController');

/**
 * 获取对话列表
 * 已迁移到Python后端API
 */
export async function listConversations(request: {
    projectId: string,
    cursor?: string,
    limit?: number,
}) {
    const user = await authCheck();

    // 使用后端API
    const response = await conversationsApiClient.list(request.projectId, {
        cursor: request.cursor,
        limit: request.limit,
    });
    
    if (!response.success || !response.data) {
        throw new Error(response.error?.message || '获取对话列表失败');
    }
    
    // 验证返回的数据格式
    const { items, nextCursor } = response.data;
    if (!Array.isArray(items)) {
        throw new Error('对话列表格式错误');
    }
    
    // 验证每个对话项
    const validatedItems = items.map(item => ListedConversationItem.parse(item));
    
    return {
        items: validatedItems,
        nextCursor: nextCursor,
    };
}

/**
 * 获取对话详情
 * 已迁移到Python后端API
 * 
 * @param conversationId - 对话ID
 * @param projectId - 项目ID（可选，如果有则使用后端API，否则使用旧实现）
 */
export async function fetchConversation(
    request: {
        conversationId: string,
        projectId?: string,
    }
) {
    const user = await authCheck();

    // 如果有projectId，使用后端API
    if (request.projectId) {
        const response = await conversationsApiClient.get(request.projectId, request.conversationId);
        if (!response.success || !response.data) {
            throw new Error(response.error?.message || '获取对话详情失败');
        }
        // 验证返回的数据格式
        return Conversation.parse(response.data);
    }
    
    // 否则使用旧实现（向后兼容）
    return await fetchConversationController.execute({
        caller: 'user',
        userId: user.id,
        conversationId: request.conversationId,
    });
}