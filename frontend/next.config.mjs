/** @type {import('next').NextConfig} */
//
// Meridian Airport PMO suite — Next.js config
// (c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
//
// `output: "standalone"` produces a self-contained .next/standalone/server.js
// in the build output. The production Dockerfile copies only that tree (plus
// .next/static + public/) into a slim node image, keeping the runtime under
// the 512 MB RAM budget on Render's free web-service tier.
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  experimental: {
    typedRoutes: false,
  },
};

export default nextConfig;
