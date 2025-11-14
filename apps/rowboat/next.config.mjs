/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone',
    // 在 Next.js 15 中，serverExternalPackages 用于排除服务端包
    // 这些包不会被打包到客户端bundle中
    serverExternalPackages: [
        'awilix',
        'mongodb',
        '@mongodb/client',
    ],
    // 注意：Next.js 15 使用 Turbopack，webpack 配置可能不生效
    // 但保留它以防回退到 webpack
    webpack: (config, { isServer }) => {
        if (!isServer) {
            // 在客户端打包时排除Node.js内置模块
            config.resolve.fallback = {
                ...config.resolve.fallback,
                child_process: false,
                net: false,
                tls: false,
                fs: false,
                crypto: false,
                stream: false,
                util: false,
                url: false,
                http: false,
                https: false,
                zlib: false,
                buffer: false,
            };
        }
        return config;
    },
    // 开发服务器端口配置（如果需要）
    // 注意：Next.js默认使用3000端口，可以通过命令行参数覆盖
    // 使用: npm run dev -- -p 3001
};

export default nextConfig;
