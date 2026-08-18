'use client';

import { Button, Icon } from '@labs/design/arey';
import Script from 'next/script';
import { FormEvent, useEffect, useRef, useState } from 'react';
import { accessLoginHref } from './public-header';

interface TurnstileApi {
  render(container: HTMLElement, options: Record<string, unknown>): string;
  reset(widgetId: string): void;
}

declare global {
  interface Window { turnstile?: TurnstileApi }
}

const siteKey = process.env.NEXT_PUBLIC_CLOUDFLARE_TURNSTILE_SITE_KEY;

interface InviteFormProps {
  inviteOpen?: boolean;
  onInviteOpenChange?: (open: boolean) => void;
}

export function InviteForm({ inviteOpen, onInviteOpenChange }: InviteFormProps) {
  const [sent, setSent] = useState(false);
  const [localInviteOpen, setLocalInviteOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [scriptReady, setScriptReady] = useState(false);
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const container = useRef<HTMLDivElement>(null);
  const widgetId = useRef<string | null>(null);
  const requestOpen = inviteOpen ?? localInviteOpen;
  const setRequestOpen = (open: boolean) => {
    setLocalInviteOpen(open);
    onInviteOpenChange?.(open);
  };

  useEffect(() => {
    if (!siteKey || !scriptReady || !container.current || !window.turnstile || widgetId.current) return;
    widgetId.current = window.turnstile.render(container.current, {
      sitekey: siteKey,
      theme: 'auto',
      callback: (token: string) => setTurnstileToken(token),
      'expired-callback': () => setTurnstileToken(null),
      'error-callback': () => setTurnstileToken(null),
    });
  }, [scriptReady]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    const form = new FormData(event.currentTarget);
    const response = await fetch('/api/v1/invite-requests', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ email: form.get('email'), note: form.get('note'), turnstileToken }),
    });
    setLoading(false);
    if (response.ok) {
      setSent(true);
    } else if (widgetId.current && window.turnstile) {
      window.turnstile.reset(widgetId.current);
      setTurnstileToken(null);
    }
  }

  return (
    <div className="ascend-login-wrap">
      <div className="ascend-login-art" aria-hidden="true">
        <div className="ascend-login-art-glass" />
        <svg viewBox="0 0 250 250" fill="none" stroke="var(--text-primary)" strokeWidth="1.1" strokeLinecap="round">
          <path d="M18 178 C 58 112, 96 68, 142 44" strokeDasharray="1400" />
          <path d="M38 202 C 88 156, 132 108, 176 54" strokeDasharray="1400" />
        </svg>
      </div>
      <div className="ascend-login-card">
        {siteKey && <Script src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit" strategy="afterInteractive" onLoad={() => setScriptReady(true)} />}
        {sent ? (
          <>
            <div className="ascend-login-card-head"><div className="ascend-login-card-title">Request sent</div><div className="ascend-login-card-description">I will review the address and reply directly.</div></div>
            <div className="ascend-login-note ascend-login-note--success"><Icon name="check" size={14} weight="bold"/><span>Your request has been recorded. Nothing else is required.</span></div>
            <Button variant="secondary" block onClick={() => { setSent(false); setRequestOpen(false); }}>Close</Button>
          </>
        ) : requestOpen ? (
          <>
            <div className="ascend-login-card-head"><div className="ascend-login-card-title">Request an invite</div><div className="ascend-login-card-description">Ascend is allowlisted one address at a time. Tell me which address to add and I’ll get back to you.</div></div>
            <form className="ascend-form" onSubmit={submit}>
              <label className="ascend-label">Google email<input name="email" type="email" required autoComplete="email" /></label>
              <label className="ascend-label">How do we know each other?<textarea name="note" maxLength={500} placeholder="How do we know each other?" /></label>
              {siteKey ? <div ref={container} /> : <p className="ascend-meta">Challenge disabled in local development.</p>}
              <div className="ascend-login-form-actions"><button className="ascend-link-button" type="button" onClick={() => setRequestOpen(false)}>Cancel</button><Button variant="primary" type="submit" loading={loading} disabled={Boolean(siteKey && !turnstileToken)}>Send request</Button></div>
            </form>
          </>
        ) : (
          <>
            <div className="ascend-login-card-head"><div className="ascend-login-card-title">Sign in</div><div className="ascend-login-card-description">Your email has to be on the allowlist. If it is, one tap and you are in — there is no password to forget.</div></div>
            <Button variant="primary" block iconLeft="google-logo" onClick={() => { window.location.href = accessLoginHref; }}>Continue with Google</Button>
            <div className="ascend-login-invite-link"><span>Not on the list yet?</span><button type="button" onClick={() => setRequestOpen(true)}>Request an invite</button></div>
            <div className="ascend-login-notes">{[
              ['eye', 'Read-only access to Gmail. Ascend never sends, moves, or deletes anything.'],
              ['hard-drives', 'Classification runs on a Mac Mini in my flat. Your mail is not sent to any API.'],
              ['prohibit', 'Message bodies are discarded after reading. Only headers and derived events are kept.'],
            ].map(([icon, text]) => <div className="ascend-login-note" key={text}><span className="ascend-login-note-icon"><Icon name={icon} size={12} weight="bold"/></span><span>{text}</span></div>)}</div>
            <div className="ascend-login-warning"><Icon name="warning" size={14} weight="bold"/><span>Google will show a “this app isn’t verified” screen. That is expected — verification would mean handing your mail to an auditor. Choose <strong>Advanced</strong>, then continue.</span></div>
          </>
        )}
      </div>
    </div>
  );
}
