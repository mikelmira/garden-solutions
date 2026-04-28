/** @type {import('next').NextConfig} */
const nextConfig = {
    output: "standalone",
    images: {
        remotePatterns: [
            {
                protocol: 'http',
                hostname: 'localhost',
                port: '8000',
                pathname: '/uploads/**',
            },
            {
                protocol: 'http',
                hostname: 'localhost',
                port: '8000',
                pathname: '/static/**',
            },
            {
                protocol: 'https',
                hostname: '*.railway.app',
                pathname: '/uploads/**',
            },
            {
                protocol: 'https',
                hostname: '*.railway.app',
                pathname: '/static/**',
            },
        ],
    },
};

module.exports = nextConfig;
