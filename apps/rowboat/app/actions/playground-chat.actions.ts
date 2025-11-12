/**
 * @deprecated 此文件中的函数已迁移到Python后端
 * @deprecated Functions in this file have been migrated to Python backend
 * 
 * 聊天功能现在通过以下方式使用：
 * Chat functionality is now accessed via:
 * - API: POST /api/v1/{project_id}/chat
 * - Client: chatApiClient (src/application/lib/chat-api-client.ts)
 * 
 * 此文件保留仅用于向后兼容，将在未来版本中删除
 * This file is kept for backward compatibility only and will be removed in a future version
 */

'use server';
import { z } from 'zod';
import { Workflow } from "../lib/types/workflow_types";
import { Message } from "@/app/lib/types/types";
import { authCheck } from './auth.actions';
import { container } from '@/di/container';
import { Conversation } from '@/src/entities/models/conversation';
import { ICreatePlaygroundConversationController } from '@/src/interface-adapters/controllers/conversations/create-playground-conversation.controller';
import { ICreateCachedTurnController } from '@/src/interface-adapters/controllers/conversations/create-cached-turn.controller';

/**
 * @deprecated 已迁移到Python后端 POST /api/v1/{project_id}/chat
 * @deprecated Migrated to Python backend POST /api/v1/{project_id}/chat
 */
export async function createConversation({
    projectId,
    workflow,
    isLiveWorkflow,
}: {
    projectId: string;
    workflow: z.infer<typeof Workflow>;
    isLiveWorkflow: boolean;
}): Promise<z.infer<typeof Conversation>> {
    const user = await authCheck();

    const controller = container.resolve<ICreatePlaygroundConversationController>("createPlaygroundConversationController");

    return await controller.execute({
        userId: user.id,
        projectId,
        workflow,
        isLiveWorkflow,
    });
}

/**
 * @deprecated 已迁移到Python后端 POST /api/v1/{project_id}/chat
 * @deprecated Migrated to Python backend POST /api/v1/{project_id}/chat
 */
export async function createCachedTurn({
    conversationId,
    messages,
}: {
    conversationId: string;
    messages: z.infer<typeof Message>[];
}): Promise<{ key: string }> {
    const user = await authCheck();
    const createCachedTurnController = container.resolve<ICreateCachedTurnController>("createCachedTurnController");

    const { key } = await createCachedTurnController.execute({
        caller: "user",
        userId: user.id,
        conversationId,
        input: {
            messages,
        },
    });

    return {
        key,
    };
}