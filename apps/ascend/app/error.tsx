'use client';
import { Button } from '@labs/design/arey';
export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) { return <main className="ascend-page ascend-page--narrow"><div className="ascend-eyebrow">Something stopped</div><h1 className="ascend-title">Ascend could not load this view</h1><p className="ascend-lede">Try the request again. If it repeats, check the service status and sync run.</p><Button onClick={reset}>Try again</Button></main>; }
