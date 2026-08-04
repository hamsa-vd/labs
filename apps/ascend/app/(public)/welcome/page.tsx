'use client';

import { Badge, Icon } from '@labs/design/arey';
import { useState } from 'react';
import { InviteForm } from '@/ui/invite-form';
import { PublicHeader } from '@/ui/public-header';

const stages = [
  ['envelope-simple', '01', 'Gmail, read only', 'A ten-minute poll pulls new message headers. Nothing is ever sent, moved, or deleted.', '1,284 seen'],
  ['funnel', '02', 'Prefilter', 'Sender domains and subject patterns score each message. Receipts and newsletters stop here.', '97% dropped'],
  ['cpu', '03', 'Local model', 'What survives goes to qwen3:8b with a JSON schema, plus a verbatim quote as evidence.', '1.2 s each'],
  ['graph', '04', 'Timeline', 'Events are appended, never edited. Status is recomputed from the whole history.', '41 applications'],
] as const;

const privacyPoints = [
  ['prohibit', 'No bodies stored', 'Subject, sender, date and the derived fields. The message text is discarded after classification.'],
  ['lock-key', 'Tokens encrypted on the Mini', 'AES-256-GCM, with the key held outside the database. A database leak gives nobody your inbox.'],
  ['trash', 'Delete actually deletes', 'One button purges your rows and revokes the Google token. No archive, no soft delete.'],
] as const;

export default function WelcomePage() {
  const [inviteOpen, setInviteOpen] = useState(false);

  return <div className="ascend-public">
    <div className="ascend-public-ambient" aria-hidden="true"><span className="ascend-ambient-a"/><span className="ascend-ambient-b"/><span className="ascend-ambient-c"/></div>
    <PublicHeader/>
    <main className="ascend-public-content">
      <section className="ascend-login-hero">
        <div className="ascend-login-copy">
          <div className="ascend-login-kicker"><Badge tone="accent" dot>Invite only</Badge><span>7 of 15 seats used</span></div>
          <h1>Your job hunt, tracked by the inbox it already lives in.</h1>
          <p>Ascend reads the application mail already sitting in your Gmail, works out what happened, and keeps the board honest. A model on my Mac Mini does the reading. Nothing you wrote ever leaves the house.</p>
          <div className="ascend-login-stats"><div><strong>7</strong><span>People on the allowlist</span></div><div><strong>0</strong><span>Emails sent to a third party</span></div><div><strong>97%</strong><span>Never touched the model</span></div></div>
        </div>
        <InviteForm inviteOpen={inviteOpen} onInviteOpenChange={setInviteOpen}/>
      </section>

      <section className="ascend-process-panel">
        <div className="ascend-section-intro"><div className="ascend-eyebrow">How it reads</div><h2>Four steps, and only one of them is a model</h2><p>Most of your mail never reaches the model at all. A plain list of sender domains and subject patterns throws out the receipts and the newsletters first, which is why this runs on a Mac Mini and not a GPU bill.</p></div>
        <div className="ascend-stage-grid"><div className="ascend-stage-flow" aria-hidden="true"><svg viewBox="0 0 1000 40" preserveAspectRatio="none"><path d="M120 20 C 200 20, 200 20, 280 20"/><path d="M370 20 C 450 20, 450 20, 530 20"/><path d="M620 20 C 700 20, 700 20, 780 20"/></svg></div>{stages.map(([icon, step, title, body, stat]) => <div className="ascend-stage-card" key={step}><div className="ascend-stage-top"><span className="ascend-stage-icon"><Icon name={icon} size={16}/></span><span>{step}</span></div><h3>{title}</h3><p>{body}</p><strong>{stat}</strong></div>)}</div>
      </section>

      <section className="ascend-local-section"><div className="ascend-local-copy"><div className="ascend-eyebrow">Why local</div><h2>The model runs in my living room, not someone’s data centre</h2><p>Gmail’s restricted-scope rules forbid handing your mail to a third-party API, and I wouldn’t want to anyway — you’re my friends. An 8B model on the Mini reads each message, returns structured JSON, and the text is gone the moment it’s done.</p><div className="ascend-privacy-points">{privacyPoints.map(([icon, title, body]) => <div key={title}><span><Icon name={icon} size={14} weight="bold"/></span><div><h3>{title}</h3><p>{body}</p></div></div>)}</div></div><div className="ascend-local-art" aria-hidden="true"><div className="ascend-local-art-glow ascend-local-art-glow-a"/><div className="ascend-local-art-glow ascend-local-art-glow-b"/><svg viewBox="0 0 420 420" fill="none" stroke="var(--text-primary)" strokeLinecap="round"><path d="M40 340 C 120 300, 150 220, 210 180 C 270 140, 320 130, 380 96"/><path d="M64 372 C 150 340, 200 268, 262 224"/><circle cx="210" cy="180" r="58"/><circle cx="210" cy="180" r="96" strokeDasharray="3 9"/></svg><div className="ascend-art-inbound"><span>inbound · gmail</span><strong>Monzo Bank Ltd</strong><b>Next steps for your application</b></div><div className="ascend-art-extraction"><span>extraction · qwen3:8b</span><div>event_type: <em>interview_invite</em></div><div>company: <em>monzo</em></div><div>confidence: <em>0.94</em></div></div><div className="ascend-art-mini"><Icon name="hard-drives" size={24}/><strong>Mac Mini</strong><span>london · offline-only</span></div></div></section>

      <section className="ascend-cta"><div><h2>Want in?</h2><p>Ascend is allowlisted, one email at a time. Message me and I’ll add you — connecting takes about a minute, and yes, Google will show you a scary unverified screen first.</p></div><div><a className="ascend-link-button" href="/privacy">Read the notice</a><button className="ascend-link-button ascend-link-button--primary" type="button" onClick={() => setInviteOpen(true)}>Request an invite <Icon name="arrow-right" size={16}/></button></div></section>
    </main>
    <footer className="ascend-public-foot"><span>ascend · self-hosted in london</span><div><a href="/privacy">Privacy notice</a><a href="/status">Status</a></div></footer>
  </div>;
}
