import { NextRequest, NextResponse } from 'next/server';
import { USE_AUTH } from '@/app/lib/feature_flags';
import { GUEST_DB_USER } from '@/app/lib/auth-client';
import { authCheck } from '@/app/actions/auth.actions';

/**
 * Auth0 Profile endpoint
 * This endpoint is called by Auth0Provider client-side to get the current user profile
 * Note: This is different from /api/auth/profile which is used by the server
 */
export async function GET(_req: NextRequest) {
    try {
        // If auth is disabled, return guest user
        if (!USE_AUTH) {
            return NextResponse.json({
                sub: GUEST_DB_USER.auth0Id,
                email: GUEST_DB_USER.email,
                email_verified: true,
                name: GUEST_DB_USER.name,
            });
        }

        // If auth is enabled, use authCheck to get the user
        const user = await authCheck();
        return NextResponse.json({
            sub: user.auth0Id,
            email: user.email,
            email_verified: true,
            name: user.name,
        });
    } catch (error) {
        // If auth fails, return guest user as fallback
        console.error('Auth profile error:', error);
        return NextResponse.json({
            sub: GUEST_DB_USER.auth0Id,
            email: GUEST_DB_USER.email,
            email_verified: true,
            name: GUEST_DB_USER.name,
        });
    }
}

