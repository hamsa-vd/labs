import Link from 'next/link';
export default function NotFound() { return <main className="ascend-page ascend-page--narrow"><div className="ascend-eyebrow">404</div><h1 className="ascend-title">This page does not exist</h1><p className="ascend-lede">The application or view may have moved.</p><Link className="ascend-link-button" href="/overview">Back to overview</Link></main>; }
