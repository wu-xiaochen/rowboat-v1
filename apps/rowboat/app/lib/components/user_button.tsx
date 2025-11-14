'use client';
import { useUser } from '@auth0/nextjs-auth0';
import { Avatar, Dropdown, DropdownItem, DropdownSection, DropdownTrigger, DropdownMenu } from "@heroui/react";
import { useRouter } from 'next/navigation';
import { USE_AUTH } from '@/app/lib/feature_flags';
import { GUEST_DB_USER } from '@/app/lib/auth-client';

export function UserButton({ useBilling, collapsed }: { useBilling?: boolean, collapsed?: boolean }) {
    const router = useRouter();
    const { user: auth0User, error: auth0Error } = useUser();
    
    // Use guest user if auth is disabled or if there's an error
    const user = !USE_AUTH || auth0Error ? {
        sub: GUEST_DB_USER.auth0Id,
        email: GUEST_DB_USER.email,
        email_verified: true,
        name: GUEST_DB_USER.name,
    } : auth0User;
    
    if (!user) {
        return <></>;
    }

    const title = user.email ?? user.name ?? 'Unknown user';
    const name = user.name ?? user.email ?? 'Unknown user';

    return <Dropdown>
        <DropdownTrigger>
            <div className="flex items-center gap-2">
                <Avatar
                    name={name}
                    size='md'
                    isBordered
                    radius='md'
                    className='shrink-0'
                />
                {!collapsed && <span className="text-sm truncate">{name}</span>}
            </div>
        </DropdownTrigger>
        <DropdownMenu
            onAction={(key) => {
                if (key === 'logout') {
                    router.push('/auth/logout');
                }
                if (key === 'billing') {
                    router.push('/billing');
                }
            }}
        >
            <DropdownSection title={title}>
                {useBilling ? (
                    <DropdownItem key="billing">
                        Billing
                    </DropdownItem>
                ) : (
                    <></>
                )}
                <DropdownItem key="logout">
                    Logout
                </DropdownItem>
            </DropdownSection>
        </DropdownMenu>
    </Dropdown>
}