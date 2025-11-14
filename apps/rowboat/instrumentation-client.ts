// instrumentation-client.js
import posthog from 'posthog-js';

// Only initialize PostHog if a token is provided
const posthogKey = process.env.NEXT_PUBLIC_POSTHOG_KEY;
const posthogHost = process.env.NEXT_PUBLIC_POSTHOG_HOST;

if (posthogKey && posthogKey.trim() !== '') {
    posthog.init(posthogKey, {
        api_host: posthogHost || 'https://app.posthog.com',
        defaults: '2025-05-24'
    });
} else {
    // PostHog is not configured, skip initialization
    // This is expected in development or when analytics is not needed
    if (process.env.NODE_ENV === 'development') {
        console.log('[PostHog] Skipping initialization: NEXT_PUBLIC_POSTHOG_KEY is not set');
    }
}