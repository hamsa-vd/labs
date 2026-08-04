import Link from 'next/link';
import Image from 'next/image';
import { ThemeToggle } from './theme-toggle';

export function PublicHeader() {
  return <header className="ascend-public-head"><Image src="/ascend-mark.png" alt="" width={26} height={26}/><strong>Ascend</strong><span className="ascend-meta">an arey product</span><div style={{marginLeft:'auto'}}><ThemeToggle/></div><Link className="ascend-link-button" href="/overview">Sign in</Link></header>;
}
