import '@hamsa-designs/arey/styles.css';
// Component CSS, harvested at build time so the server renders styled HTML.
// arey injects it at runtime otherwise, which means SSR ships unstyled markup.
// See architecture §12.1 and scripts/extract-design-system-css.ts.
import '@/generated/arey-components.css';
import type { Metadata, Viewport } from 'next';
import type { ReactNode } from 'react';

export const metadata: Metadata = {
  title: {
    default: 'Ascend',
    template: '%s · Ascend',
  },
  description: 'Private job-application tracking from Gmail-derived events.',
  applicationName: 'Ascend',
};

export const viewport: Viewport = {
  themeColor: '#000000',
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" data-theme="dark">
      <body>{children}</body>
    </html>
  );
}
