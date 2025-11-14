/**
 * 客户端安全的认证相关常量
 * Client-safe authentication constants
 * 
 * 这个文件包含了可以在客户端组件中安全使用的认证相关常量
 * This file contains authentication-related constants that can be safely used in client components
 */

import { User } from "@/src/entities/models/user";
import { z } from "zod";

/**
 * Guest 用户常量（客户端安全）
 * Guest user constant (client-safe)
 */
export const GUEST_DB_USER: z.infer<typeof User> = {
    id: "guest_user",
    auth0Id: "guest_user",
    name: "Guest",
    email: "wuxiaochen0802@gmail.com",
    createdAt: new Date().toISOString(),
};

/**
 * Guest 会话常量（客户端安全）
 * Guest session constant (client-safe)
 */
export const GUEST_SESSION = {
    email: "wuxiaochen0802@gmail.com",
    email_verified: true,
    sub: "guest_user",
};

