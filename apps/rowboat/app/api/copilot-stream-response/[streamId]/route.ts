import { container } from "@/di/container";
import { IRunCopilotCachedTurnController } from "@/src/interface-adapters/controllers/copilot/run-copilot-cached-turn.controller";
import { requireAuth } from "@/app/lib/auth";

export const maxDuration = 300;

export async function GET(request: Request, props: { params: Promise<{ streamId: string }> }) {
  const params = await props.params;

  // get user data
  const user = await requireAuth();

  const runCopilotCachedTurnController = container.resolve<IRunCopilotCachedTurnController>("runCopilotCachedTurnController");

  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      try {
        let eventCount = 0;
        let hasContent = false;
        
        // Iterate over the copilot stream generator
        for await (const event of runCopilotCachedTurnController.execute({
          caller: "user",
          userId: user.id,
          apiKey: request.headers.get("Authorization")?.split(" ")[1],
          key: params.streamId,
        })) {
          eventCount++;
          
          // Log first few events for debugging
          if (eventCount <= 5) {
            const eventType = (event as any).type;
            const eventContent = (event as any).content;
            console.log(`📦 SSE EVENT #${eventCount}:`, { 
              type: eventType || 'unknown',
              hasContent: !!eventContent,
              contentLength: eventContent?.length || 0,
              keys: Object.keys(event)
            });
          }
          
          // Check if this is a content event
          const eventAny = event as any;
          if (eventAny.content) {
            hasContent = true;
            controller.enqueue(encoder.encode(`event: message\ndata: ${JSON.stringify(event)}\n\n`));
          } else if (eventAny.type === 'tool-call') {
            controller.enqueue(encoder.encode(`event: tool-call\ndata: ${JSON.stringify(event)}\n\n`));
          } else if (eventAny.type === 'tool-result') {
            controller.enqueue(encoder.encode(`event: tool-result\ndata: ${JSON.stringify(event)}\n\n`));
          } else {
            // Log unknown events but don't fail
            console.log(`⚠️ UNKNOWN SSE EVENT:`, { type: eventAny.type || 'unknown', keys: Object.keys(event) });
          }
        }
        
        console.log(`📊 SSE STREAM SUMMARY:`, {
          totalEvents: eventCount,
          hasContent,
          streamId: params.streamId
        });
      } catch (error) {
        console.error('❌ Error processing copilot stream:', error);
        controller.error(new Error("Something went wrong. Please try again."));
      } finally {
        console.log("🔚 closing stream");
        // Always send done event, even if no content was generated
        controller.enqueue(encoder.encode(`event: done\ndata: ${JSON.stringify({ type: 'done' })}\n\n`));
        controller.enqueue(encoder.encode("event: end\n\n"));
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
    },
  });
}