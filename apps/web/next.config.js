/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // Only proxy /api to localhost backend during local development.
    // In production, NEXT_PUBLIC_API_URL (baked at build time) points to the
    // Render-hosted FastAPI backend, so no rewrite is needed.
    return [
      {
        source: "/api/:path*",
        has: [{ type: "header", key: "x-local-dev" }],
        destination: "http://localhost:8000/api/:path*",
      },
    ];
  },
};
module.exports = nextConfig;
