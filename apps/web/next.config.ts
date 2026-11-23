import type { NextConfig } from 'next';
const config: NextConfig = {
  transpilePackages: ['@amvs/domain', '@amvs/composition'],
  poweredByHeader: false,
};
export default config;
