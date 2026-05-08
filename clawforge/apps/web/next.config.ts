import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  transpilePackages: ['@clawforge/ui', '@clawforge/types'],
  experimental: {
    // Enable server actions
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },
  // Proxy API requests to FastAPI backend
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: process.env.API_URL
          ? `${process.env.API_URL}/api/v1/:path*`
          : 'http://localhost:8000/api/v1/:path*',
      },
    ];
  },
};

export default nextConfig;
