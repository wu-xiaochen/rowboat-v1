import { NextFetchEvent, NextRequest, NextResponse } from "next/server";
import { auth0 } from "./app/lib/auth0";

const corsOptions = {
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, x-client-id, Authorization',
}

async function authCheck(request: NextRequest) {
  const session = await auth0.getSession(request);
  const loginUrl = new URL('/auth/login', request.url);
  loginUrl.searchParams.set('returnTo', request.nextUrl.pathname + request.nextUrl.search);
  if (!session) {
    return NextResponse.redirect(loginUrl);
  }
  return auth0.middleware(request);
}

export async function middleware(request: NextRequest, event: NextFetchEvent) {
  // Redirect root path to /projects if auth is disabled
  if (request.nextUrl.pathname === '/') {
    if (!process.env.USE_AUTH || process.env.USE_AUTH !== 'true') {
      return NextResponse.redirect(new URL('/projects', request.url));
    }
  }

  // Check if the request path starts with /auth
  // Skip Auth0 middleware if USE_AUTH is disabled, except for /auth/profile which we handle ourselves
  if (request.nextUrl.pathname.startsWith('/auth')) {
    // If auth is disabled, allow /auth/profile to be handled by our route handler
    if (!process.env.USE_AUTH && request.nextUrl.pathname === '/auth/profile') {
      return NextResponse.next();
    }
    // Otherwise, use Auth0 middleware
    if (process.env.USE_AUTH === 'true') {
      return await auth0.middleware(request);
    }
    // If auth is disabled and it's not /auth/profile, skip Auth0 middleware
    return NextResponse.next();
  }

  // Check if the request path starts with /api/
  if (request.nextUrl.pathname.startsWith('/api/')) {
    // Handle preflighted requests
    if (request.method === 'OPTIONS') {
      const preflightHeaders = {
        'Access-Control-Allow-Origin': '*',
        ...corsOptions,
      }
      return NextResponse.json({}, { headers: preflightHeaders });
    }

    // Handle simple requests
    const response = NextResponse.next();

    // Set CORS headers for all origins
    response.headers.set('Access-Control-Allow-Origin', '*');

    Object.entries(corsOptions).forEach(([key, value]) => {
      response.headers.set(key, value);
    })

    return response;
  }

  if (request.nextUrl.pathname.startsWith('/projects') ||
    request.nextUrl.pathname.startsWith('/billing') ||
    request.nextUrl.pathname.startsWith('/onboarding')) {
    // Skip auth check if USE_AUTH is not enabled
    if (process.env.USE_AUTH === 'true') {
      return await authCheck(request);
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico, sitemap.xml, robots.txt (metadata files)
     */
    "/((?!_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt).*)",
  ],
};