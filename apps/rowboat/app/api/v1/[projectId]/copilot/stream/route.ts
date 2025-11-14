import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/app/lib/auth";

export const maxDuration = 300;

/**
 * Copilot流式响应代理端点
 * 代理到后端Python API
 */
export async function POST(
    req: NextRequest,
    { params }: { params: Promise<{ projectId: string }> }
): Promise<Response> {
    const { projectId } = await params;
    
    // 获取用户认证
    const user = await requireAuth();
    
    // 获取请求体
    const body = await req.json();
    
    // 获取后端API URL
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';
    
    try {
        // 代理请求到后端
        const response = await fetch(`${API_BASE_URL}/api/v1/${projectId}/copilot/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': req.headers.get('Authorization') || `Bearer ${user.id}`,
            },
            body: JSON.stringify(body),
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
            return NextResponse.json(
                { error: errorData.error || `HTTP ${response.status}` },
                { status: response.status }
            );
        }
        
        // 返回流式响应
        return new Response(response.body, {
            headers: {
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
            },
        });
    } catch (error) {
        console.error('❌ Error proxying copilot stream:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Unknown error' },
            { status: 500 }
        );
    }
}

