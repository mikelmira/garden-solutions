/** @type {import('next').NextConfig} */
const nextConfig = {
    // NOTE: standalone output is intentionally NOT enabled here. Next.js's
    // standalone tracing has long-standing issues with pnpm workspaces (the
    // node_modules symlinks land at wrong relative depth and the `.pnpm`
    // store is left empty in the traced output). The Dockerfile installs
    // production deps in the runner stage and runs `next start` instead.
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
