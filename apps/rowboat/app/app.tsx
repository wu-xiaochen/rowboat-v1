'use client';
import Image from 'next/image';
import logo from "@/public/logo.svg";
import { useUser } from "@auth0/nextjs-auth0";
import { useRouter } from "next/navigation";
import { Spinner } from "@heroui/react";
import { USE_AUTH } from "@/app/lib/feature_flags";
import { GUEST_DB_USER } from "@/app/lib/auth-client";

export function App() {
    const router = useRouter();
    const { user: auth0User, isLoading: auth0Loading, error: auth0Error } = useUser();
    
    // Use guest user if auth is disabled or if there's an error
    const user = !USE_AUTH || auth0Error ? {
        sub: GUEST_DB_USER.auth0Id,
        email: GUEST_DB_USER.email,
        email_verified: true,
        name: GUEST_DB_USER.name,
    } : auth0User;
    const isLoading = USE_AUTH ? auth0Loading : false;

    if (user) {
        router.push("/projects");
    }

    // Add auto-redirect for non-authenticated users (only if auth is enabled)
    if (USE_AUTH && !isLoading && !user) {
        router.push("/auth/login");
    }

    return (
        <div className="min-h-screen w-full bg-[url('/landing-bg.jpg')] bg-cover bg-center flex flex-col items-center justify-between py-10">
            {/* Main content box */}
            <div className="flex-1 flex items-center justify-center">
                <div className="bg-white/70 backdrop-blur-sm rounded-xl p-10 flex flex-col items-center gap-8 shadow-lg">
                    <Image
                        src={logo}
                        alt="质信智购 Logo"
                        height={40}
                        width={120}
                    />
                    {(isLoading || !user) && <Spinner size="sm" />}
                    {user && <div className="flex items-center gap-2">
                        <Spinner size="sm" />
                        <div className="text-sm text-gray-400">欢迎, {user.name}</div>
                    </div>}
                </div>
            </div>

            {/* Footer */}
            <div className="flex flex-col items-center gap-2 text-xs text-white/70">
                <div>&copy; 2025 质信智购</div>
            </div>
        </div>
    );
}
