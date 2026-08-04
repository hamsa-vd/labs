import type { ReactNode } from 'react';
import { redirect } from 'next/navigation';
import { currentUser } from '@/auth/access';
import { AppShell } from '@/ui/app-shell';

export const dynamic = 'force-dynamic';

export default async function AuthenticatedLayout({ children }: Readonly<{ children: ReactNode }>) {
  const user = await currentUser();
  if (!user) redirect('/no-access');
  return <AppShell email={user.email}>{children}</AppShell>;
}
