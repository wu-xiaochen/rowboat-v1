import { NextRequest } from "next/server";
import { z } from "zod";
import { ApiResponse } from "@/app/lib/types/api_types";
import { ApiRequest } from "@/app/lib/types/api_types";
import { PrefixLogger } from "../../../../lib/utils";

/**
 * 聊天API路由 - 代理到后端
 * Chat API route - proxy to backend
 * 
 * 注意：此路由现在完全代理到后端API，不再使用前端的agents runtime
 * Note: This route now fully proxies to backend API, no longer using frontend agents runtime
 */
export async function POST(
    req: NextRequest,
    { params }: { params: Promise<{ projectId: string }> }
): Promise<Response> {
    const { projectId } = await params;
    const requestId = crypto.randomUUID();
    const logger = new PrefixLogger(`chat-proxy:${requestId}`);

    try {
        // 解析请求体
        const body = await req.json();
        const data = ApiRequest.parse(body);
    const { conversationId, messages, mockTools, stream } = data;

        // 获取后端API地址
        const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';
        const backendUrl = `${API_BASE_URL}/api/v1/${projectId}/chat`;

        // 构建请求头
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        };

        // 传递Authorization头（如果存在）
        const authHeader = req.headers.get("Authorization");
        if (authHeader) {
            headers['Authorization'] = authHeader;
        }

        // 构建请求体
        const requestBody = {
            conversation_id: conversationId,
            messages: messages,
            mock_tools: mockTools,
        stream: Boolean(stream),
        };

        logger.log(`Proxying request to backend: ${backendUrl}`);

        // 转发请求到后端
        const backendResponse = await fetch(backendUrl, {
            method: 'POST',
            headers,
            body: JSON.stringify(requestBody),
        });

        // 如果是流式响应，直接转发流
        if (stream && backendResponse.body) {
            return new Response(backendResponse.body, {
                status: backendResponse.status,
            headers: {
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        });
    }

        // 非流式响应
        if (!backendResponse.ok) {
            const errorData = await backendResponse.json().catch(() => ({ error: 'Unknown error' }));
            logger.log(`Backend error: ${JSON.stringify(errorData)}`);
            return Response.json(
                { error: errorData.error || errorData.detail || 'Backend request failed' },
                { status: backendResponse.status }
            );
    }

        const responseData = await backendResponse.json();
        
        // 转换后端响应格式为前端格式
    const responseBody: z.infer<typeof ApiResponse> = {
            conversationId: responseData.data?.conversation_id || responseData.conversation_id,
            turn: responseData.data?.turn || responseData.turn,
    };

    return Response.json(responseBody);

    } catch (e) {
        logger.log(`Error in chat proxy: ${e}`);
        if (e instanceof z.ZodError) {
            return Response.json({ error: `Invalid request: ${e.message}` }, { status: 400 });
        }
        return Response.json({ error: "Internal server error" }, { status: 500 });
    }
}
