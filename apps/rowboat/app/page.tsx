import { App } from "./app";
import { USE_AUTH } from "./lib/feature_flags";

export const dynamic = 'force-dynamic';

export default function Home() {
    // If auth is disabled, middleware will redirect to /projects
    // So this component should only render when USE_AUTH is true
    // But we still check here as a fallback
    if (!USE_AUTH) {
        // This should never be reached because middleware handles the redirect
        // But if it is, we'll just render the App component which will redirect client-side
        return <App />
    }
    return <App />
}