'use client';
import { Icon, IconButton, Kbd } from '@labs/design/arey';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import type { ReactNode } from 'react';
import { ThemeToggle } from './theme-toggle';
import { SyncButton } from './sync-button';

const nav = [
  ['/overview','Overview','squares-four'], ['/applications','Applications','briefcase'],
  ['/timeline','Timeline','clock-counter-clockwise'], ['/review','Needs review','seal-question'],
  ['/sync-runs','Sync runs','arrows-clockwise'], ['/settings','Settings','sliders-horizontal'],
] as const;

export function AppShell({ email, children }: { email: string; children: ReactNode }) {
  const pathname = usePathname();
  const title = nav.find(([href]) => pathname.startsWith(href))?.[1] ?? 'Ascend';
  const initials = email.split('@')[0].split(/[._-]+/).filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join('') || 'A';
  const signOut = (size: 'sm' | 'md' = 'sm') => <Link className={`arey-iconbtn${size === 'sm' ? ' arey-iconbtn--sm' : ''}`} href="/cdn-cgi/access/logout" aria-label="Sign out"><Icon name="sign-out" size={size === 'md' ? 16 : 14}/></Link>;
  const sidebarToggle = (label: string, size: 'sm' | 'md' = 'sm') => <label className={`arey-iconbtn${size === 'sm' ? ' arey-iconbtn--sm' : ''} ascend-sidebar-toggle-control`} htmlFor="ascend-sidebar-toggle" aria-label={label}><Icon name="sidebar-simple" size={size === 'md' ? 16 : 14}/></label>;
  const item = ([href,label,icon]: typeof nav[number]) => <Link key={href} href={href} className="ascend-nav-link" aria-current={pathname.startsWith(href) ? 'page' : undefined}><Icon name={icon} weight={pathname.startsWith(href) ? 'fill' : 'regular'} /><span>{label}</span></Link>;
  return <div className="ascend-shell">
    <input className="ascend-sidebar-toggle-input" id="ascend-sidebar-toggle" type="checkbox" aria-label="Toggle sidebar" />
    <div className="ascend-authenticated-ambient" aria-hidden="true"><span className="ascend-ambient-a"/><span className="ascend-ambient-b"/><span className="ascend-ambient-c"/></div>
    <aside className="ascend-sidebar ascend-sidebar--collapsed">
      <div className="ascend-sidebar-mark"><Image src="/ascend-mark.png" alt="Ascend" width={22} height={22}/></div>
      <nav className="ascend-nav">{nav.map(([href, label, icon]) => <Link key={href} href={href} className="ascend-nav-link" aria-label={label} aria-current={pathname.startsWith(href) ? 'page' : undefined}><Icon name={icon} weight={pathname.startsWith(href) ? 'fill' : 'regular'} /></Link>)}</nav>
      <div className="ascend-sidebar-foot ascend-sidebar-foot--collapsed"><span className="ascend-sync-dot" title="Sync status"/>{sidebarToggle('Expand sidebar', 'md')}{signOut('md')}</div>
    </aside>
    <aside className="ascend-sidebar ascend-sidebar--expanded">
      <div className="ascend-brand"><Link href="/overview" className="ascend-brand-link"><Image src="/ascend-mark.png" alt="" width={24} height={24}/><strong>Ascend</strong></Link>{sidebarToggle('Collapse sidebar')}</div>
      <nav className="ascend-nav"><div className="ascend-nav-label">Tracker</div>{nav.map(item)}</nav>
      <div className="ascend-sidebar-foot">
        <div className="ascend-sync-card"><div><span className="ascend-sync-dot"/><strong>Sync status</strong></div><span>Connect Gmail to start</span></div>
        <div className="ascend-account"><span className="ascend-account-avatar" aria-hidden="true">{initials}</span><div className="ascend-account-copy"><strong>{email.split('@')[0]}</strong><span>{email}</span></div>{signOut()}</div>
      </div>
    </aside>
    <div className="ascend-main"><header className="ascend-topbar"><nav className="ascend-breadcrumbs" aria-label="Breadcrumb"><Link href="/overview">Ascend</Link><span aria-hidden="true">/</span><span aria-current="page">{title}</span></nav><Link className="ascend-topbar-search" href="/applications" aria-label="Search companies, roles"><Icon name="magnifying-glass" size={14}/><span>Search companies, roles</span><Kbd keys={['cmd', 'K']} /></Link><div className="ascend-topbar-actions"><ThemeToggle/><IconButton icon="bell" label="Notifications"/><SyncButton/></div></header>{children}</div>
    <nav className="ascend-mobile-nav">{nav.filter(([href]) => href !== '/sync-runs').map(item)}</nav>
  </div>;
}
