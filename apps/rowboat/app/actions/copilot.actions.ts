'use server';
import {
    CopilotAPIRequest,
    CopilotChatContext, CopilotMessage,
    DataSourceSchemaForCopilot,
} from "../../src/entities/models/copilot";
import { 
    Workflow} from "../lib/types/workflow_types";
import { z } from 'zod';
import { projectAuthCheck } from "./project.actions";
import { authCheck } from "./auth.actions";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';

/**
 * 获取Copilot流式响应
 * 注意：现在前端直接调用API，这个函数主要用于验证和错误处理
 * 返回一个简单的成功标识，实际流式响应由前端直接处理
 */
export async function getCopilotResponseStream(
    projectId: string,
    messages: z.infer<typeof CopilotMessage>[],
    current_workflow_config: z.infer<typeof Workflow>,
    context: z.infer<typeof CopilotChatContext> | null,
    dataSources?: z.infer<typeof DataSourceSchemaForCopilot>[]
): Promise<{
    streamId: string;
} | { billingError: string }> {
    // 验证用户认证
    await authCheck();
    
    // 验证项目权限
    await projectAuthCheck(projectId);
    
    // 返回成功标识（前端会直接调用API）
    // streamId仅用于兼容性，不会被实际使用
    return { streamId: 'direct-api-call' };
        }

/**
 * 获取编辑智能体提示词
 * 直接调用后端API
 */
export async function getCopilotAgentInstructions(
    projectId: string,
    messages: z.infer<typeof CopilotMessage>[],
    current_workflow_config: z.infer<typeof Workflow>,
    agentName: string,
): Promise<string | { billingError: string }> {
    await projectAuthCheck(projectId);

    const user = await authCheck();

    try {
        // 构建请求体
        const requestBody = {
        projectId,
        messages,
            workflow: current_workflow_config as any,
        context: {
                type: 'agent' as const,
            name: agentName,
            },
        };

        // 调用后端API
        const response = await fetch(`${API_BASE_URL}/api/v1/${projectId}/copilot/edit-agent-instructions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${user.id}`, // 使用用户ID作为临时token
            },
            body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
            if (errorData.error?.includes('billing') || errorData.error?.includes('credits')) {
                return { billingError: errorData.error || 'Billing error' };
            }
            throw new Error(errorData.error || `HTTP ${response.status}`);
    }

        const data = await response.json();
        return data.agentInstructions || data.agent_instructions || '';
    } catch (err: any) {
        if (err.message?.includes('billing') || err.message?.includes('credits')) {
            return { billingError: err.message };
        }
        throw err;
    }
}