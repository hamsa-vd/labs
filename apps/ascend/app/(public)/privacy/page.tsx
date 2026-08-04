/**
 * Not decoration. This page is the informed-consent record the architecture
 * requires before anyone connects a Gmail account. See §7 and §11.5.8.
 */
export default function PrivacyNoticePage() {
  return <div className="ascend-public"><PublicHeader/><main className="ascend-page ascend-page--narrow"><div className="ascend-eyebrow">Privacy notice · 3 August 2026</div><h1 className="ascend-title">What Ascend reads and keeps</h1><p className="ascend-lede">Ascend uses Gmail read-only access to find job-application messages for you. Use of information received from Google Workspace APIs adheres to the Google API Services User Data Policy, including Limited Use requirements.</p><div className="ascend-stack" style={{marginTop:'var(--space-8)'}}><Card title="Processed, then discarded"><p>Message bodies are fetched only for likely job mail, cleaned, classified locally, and discarded. They are not written to Postgres, logs, analytics, or backups.</p></Card><Card title="What is retained"><p>Gmail message and thread IDs, sender, subject, timestamp, prefilter result, structured application events, and cryptographic hashes used to verify evidence fetched later.</p></Card><Card title="Where processing happens"><p>Classification runs through Ollama on the operator’s Mac Mini. Email content is not sent to OpenAI, Anthropic, or another hosted model.</p></Card><Card title="Delete means delete"><p>Deleting your account attempts to revoke Google access, destroys the encrypted refresh token, and cascades deletion through your Ascend rows. Access allowlisting is revoked separately by the operator.</p></Card></div></main></div>;
}
import { Card } from '@labs/design/arey';
import { PublicHeader } from '@/ui/public-header';
