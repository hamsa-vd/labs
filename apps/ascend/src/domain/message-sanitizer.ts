import * as cheerio from 'cheerio';
import { createHash } from 'node:crypto';

export const SANITIZER_VERSION = 1;
export const MAX_CLEANED_CODE_POINTS = 2_000;

const INVISIBLE_UNICODE = /[\u200B-\u200F\u202A-\u202E\u2060-\u206F\uFEFF]/g;
const HIDDEN_STYLE = /(?:^|;)\s*(?:display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0(?:\.0+)?\s*(?:!important)?|font-size\s*:\s*0(?:px|em|rem|%)?\s*(?:!important)?|(?:width|height)\s*:\s*0(?:px|em|rem|%)?\s*(?:!important)?)\s*(?:;|$)/i;
const QUOTED_REPLY = /(?:^|\n)(?:On .{0,180} wrote:|From:\s.+\nSent:\s.+\n|>{1,}\s?)/i;
const FOOTER = /(?:^|\n)(?:unsubscribe|manage (?:your )?preferences)\b/i;

export interface SanitizedMessage {
  text: string;
  contentSha256: string;
  version: number;
}

export interface EvidenceLocation {
  offset: number;
  length: number;
  sha256: string;
  sanitizerVersion: number;
}

function truncateCodePoints(value: string): string {
  return Array.from(value).slice(0, MAX_CLEANED_CODE_POINTS).join('');
}

function sanitizeMessageHtmlV1(html: string): SanitizedMessage {
  const $ = cheerio.load(html);
  $('script,style,noscript,template,[hidden],[aria-hidden="true"]').remove();
  $('*').each((_, element) => {
    const style = $(element).attr('style');
    if (style && HIDDEN_STYLE.test(style)) $(element).remove();
  });
  $('*').contents().filter((_, node) => node.type === 'comment').remove();
  $('br').replaceWith('\n');
  $('p,div,section,article,header,footer,li,tr,blockquote').append('\n');

  let text = $.root().text().normalize('NFKC').replace(INVISIBLE_UNICODE, '');
  const quoted = text.search(QUOTED_REPLY);
  if (quoted >= 0) text = text.slice(0, quoted);
  const footer = text.search(FOOTER);
  if (footer >= 0) text = text.slice(0, footer);
  text = truncateCodePoints(text.replace(/\s+/g, ' ').trim());

  return {
    text,
    contentSha256: createHash('sha256').update(text).digest('hex'),
    version: SANITIZER_VERSION,
  };
}

export function sanitizeMessageHtml(html: string): SanitizedMessage {
  return sanitizeMessageHtmlV1(html);
}

/** Keep previous implementations addressable so stored evidence locations remain reproducible. */
export function sanitizeMessageHtmlVersion(html: string, version: number): SanitizedMessage | null {
  if (version === 1) return sanitizeMessageHtmlV1(html);
  return null;
}

export function locateEvidence(cleanedText: string, evidence: string, sanitizerVersion = SANITIZER_VERSION): EvidenceLocation | null {
  const start = cleanedText.indexOf(evidence);
  if (start < 0) return null;
  return {
    offset: start,
    length: evidence.length,
    sha256: createHash('sha256').update(evidence).digest('hex'),
    sanitizerVersion,
  };
}
