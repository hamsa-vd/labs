import type { NextConfig } from 'next';

/**
 * `transpilePackages` is required, not optional. @hamsa-designs/arey exports raw
 * .jsx from node_modules ("./react" -> "./components/index.jsx") and SWC skips
 * node_modules by default, so the first component import fails the build.
 */
const securityHeaders = [
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
];

const nextConfig: NextConfig = {
  output: 'standalone',
  poweredByHeader: false,
  reactStrictMode: true,
  transpilePackages: ['@hamsa-designs/arey'],
  async headers() {
    return [{ source: '/:path*', headers: securityHeaders }];
  },
};

export default nextConfig;
