import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8001";
    return [
      {
        source: "/api/v1/:path*",
        destination: `${apiUrl}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
