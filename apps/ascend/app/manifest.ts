import type { MetadataRoute } from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'Ascend',
    short_name: 'Ascend',
    description: 'Private job-application tracking from Gmail-derived events.',
    start_url: '/overview',
    display: 'standalone',
    background_color: '#000000',
    theme_color: '#000000',
  };
}
