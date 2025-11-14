/**
 * ⚠️ 已弃用：此 Use Case 使用旧的 Agents Runtime
 * ⚠️ DEPRECATED: This Use Case uses the old Agents Runtime
 * 
 * 注意：前端的 API 路由（/api/v1/[projectId]/chat/route.ts）已经改为代理到后端
 * 此 Use Case 可能仍被某些内部代码使用，但新的请求应该通过后端 API
 * 
 * Note: Frontend API route (/api/v1/[projectId]/chat/route.ts) has been changed to proxy to backend
 * This Use Case may still be used by some internal code, but new requests should go through backend API
 */

import { Reason, Turn, TurnEvent } from "@/src/entities/models/turn";
import { USE_BILLING } from "@/app/lib/feature_flags";
import { authorize, getCustomerIdForProject, logUsage, UsageTracker } from "@/app/lib/billing";
import { NotFoundError } from '@/src/entities/errors/common';
import { IConversationsRepository } from "@/src/application/repositories/conversations.repository.interface";
// ⚠️ 已弃用：使用旧的 agents runtime
// ⚠️ DEPRECATED: Using old agents runtime
import { streamResponse } from "@/src/application/lib/agents-runtime/agents";
import { z } from "zod";
import { Message } from "@/app/lib/types/types";
import { IUsageQuotaPolicy } from '../../policies/usage-quota.policy.interface';
import { IProjectActionAuthorizationPolicy } from '../../policies/project-action-authorization.policy';

const inputSchema = z.object({
    caller: z.enum(["user", "api", "job_worker"]),
    userId: z.string().optional(),
    apiKey: z.string().optional(),
    conversationId: z.string(),
    reason: Reason,
    input: Turn.shape.input,
});

export interface IRunConversationTurnUseCase {
    execute(data: z.infer<typeof inputSchema>): AsyncGenerator<z.infer<typeof TurnEvent>, void, unknown>;
}

export class RunConversationTurnUseCase implements IRunConversationTurnUseCase {
    private readonly conversationsRepository: IConversationsRepository;
    private readonly usageQuotaPolicy: IUsageQuotaPolicy;
    private readonly projectActionAuthorizationPolicy: IProjectActionAuthorizationPolicy;

    constructor({
        conversationsRepository,
        usageQuotaPolicy,
        projectActionAuthorizationPolicy,
    }: {
        conversationsRepository: IConversationsRepository,
        usageQuotaPolicy: IUsageQuotaPolicy,
        projectActionAuthorizationPolicy: IProjectActionAuthorizationPolicy,
    }) {
        this.conversationsRepository = conversationsRepository;
        this.usageQuotaPolicy = usageQuotaPolicy;
        this.projectActionAuthorizationPolicy = projectActionAuthorizationPolicy;
    }

    async *execute(data: z.infer<typeof inputSchema>): AsyncGenerator<z.infer<typeof TurnEvent>, void, unknown> {
        // fetch conversation
        const conversation = await this.conversationsRepository.fetch(data.conversationId);
        if (!conversation) {
            throw new NotFoundError('Conversation not found');
        }

        // extract projectid from conversation
        const { id: conversationId, projectId } = conversation;

        // authz check
        if (data.caller !== "job_worker") {
            await this.projectActionAuthorizationPolicy.authorize({
                caller: data.caller,
                userId: data.userId,
                apiKey: data.apiKey,
                projectId,
            });
        }

        // assert and consume quota
        await this.usageQuotaPolicy.assertAndConsumeProjectAction(projectId);

        // Check billing auth
        let billingCustomerId: string | null = null;
        if (USE_BILLING) {
            // get billing customer id for project
            billingCustomerId = await getCustomerIdForProject(projectId);

            // validate enough credits
            const result = await authorize(billingCustomerId, {
                type: "use_credits"
            });
            if (!result.success) {
                yield {
                    type: "error",
                    error: result.error || 'Billing error',
                    isBillingError: true,
                };
                return;
            }

            // validate model usage
            const agentModels = conversation.workflow.agents.reduce((acc, agent) => {
                acc.push(agent.model);
                return acc;
            }, [] as string[]);
            const response = await authorize(billingCustomerId, {
                type: 'agent_response',
                data: {
                    agentModels,
                },
            });
            if (!response.success) {
                yield {
                    type: "error",
                    error: response.error || 'Billing error',
                    isBillingError: true,
                };
                return;
            }
        }

        // set timestamps where missing
        data.input.messages.forEach(msg => {
            if (!msg.timestamp) {
                msg.timestamp = new Date().toISOString();
            }
        });

        // fetch previous conversation turns and pull message history
        const previousMessages = conversation.turns?.flatMap(t => [
            ...t.input.messages,
            ...t.output,
        ]);
        const inputMessages = [
            ...previousMessages || [],
            ...data.input.messages,
        ]

        // override mock tools if requested
        if (data.input.mockTools) {
            conversation.workflow.mockTools = data.input.mockTools;
        }

        // init usage tracker
        const usageTracker = new UsageTracker();

        // ⚠️ 已弃用：直接调用旧的 agents runtime
        // ⚠️ DEPRECATED: Directly calling old agents runtime
        // 新的实现应该调用后端 API: POST /api/v1/{project_id}/chat
        // New implementation should call backend API: POST /api/v1/{project_id}/chat
        try {
            const outputMessages: z.infer<typeof Message>[] = [];
            for await (const event of streamResponse(projectId, conversation.workflow, inputMessages, usageTracker)) {
                // handle msg events
                if ("role" in event) {
                    // collect generated message
                    const msg = {
                        ...event,
                        timestamp: new Date().toISOString(),
                    };
                    outputMessages.push(msg);

                    // yield event
                    yield {
                        type: "message",
                        data: msg,
                    };
                }
            }

            // save turn data
            const turn = await this.conversationsRepository.addTurn(data.conversationId, {
                reason: data.reason,
                input: data.input,
                output: outputMessages,
            });

            // yield event
            yield {
                type: "done",
                turn,
                conversationId,
            }
        } finally {
            // Log billing usage
            console.log('finally logging billing usage');
            if (USE_BILLING && billingCustomerId) {
                await logUsage(billingCustomerId, {
                    items: usageTracker.flush(),
                });
            }
        }
    }
}