// arey tokens, fonts, and component CSS — pre-harvested by @labs/design so SSR
// renders styled HTML. See packages/typescript/design/scripts/build-arey-css.ts.
import '@labs/design/arey.css';
import './ascend.css';
import { ThemeScript } from '@labs/design';
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
    <html lang="en" data-theme="dark" suppressHydrationWarning>
      <head>
        {/* Required before hydration so the global theme is applied without Next's client stream. */}
        <ThemeScript src="/api/labs-theme" />
      </head>
      <body>{children}</body>
    </html>
  );
}
