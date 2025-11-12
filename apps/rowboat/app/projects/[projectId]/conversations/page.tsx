import { Metadata } from "next";
import { requireActiveBillingSubscription } from '@/app/lib/billing';
import { ConversationsList } from "./components/conversations-list";

export const metadata: Metadata = {
    title: "对话",
};

export default async function Page(
    props: {
        params: Promise<{ projectId: string }>
    }
) {
    const params = await props.params;
    await requireActiveBillingSubscription();
    return <ConversationsList projectId={params.projectId} />;
}


