/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone',
    serverExternalPackages: [
        'awilix',
    ],
    // 开发服务器端口配置（如果需要）
    // 注意：Next.js默认使用3000端口，可以通过命令行参数覆盖
    // 使用: npm run dev -- -p 3001
};

export default nextConfig;
