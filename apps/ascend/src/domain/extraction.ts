import { z } from 'zod';
import { applicationEventTypes, isApplicationStatus } from './application-event';

/**
 * The contract the local model must satisfy. Passed to Ollama as a JSON schema
 * so decoding is constrained: `eventType` cannot be anything but the enum, and
 * the only free-text channels are company, roleTitle, evidence and reason.
 * See architecture §6.2 and §13.
 */
export const extractionSchema = z.object({
  isJobRelated: z.boolean(),
  company: z.string().nullable(),
  roleTitle: z.string().nullable(),
  eventType: z.enum(applicationEventTypes),
  occurredAtHint: z.string().nullable(),
  /** Interview or call booking. ISO 8601, resolved against the message date. */
  scheduledAt: z.string().nullable(),
  /** Assessment or offer-response deadline. ISO 8601. */
  deadlineAt: z.string().nullable(),
  confidence: z.number().min(0).max(1),
  /** Verbatim quote from the cleaned source supporting eventType. */
  evidence: z.string(),
  /** One sentence on why this was ambiguous, empty when it was not. */
  reason: z.string(),
});

export type Extraction = z.infer<typeof extractionSchema>;

export type ExtractionVerdict =
  | { outcome: 'accepted'; extraction: Extraction }
  | { outcome: 'needs_review'; extraction: Extraction; failures: string[] }
  | { outcome: 'discarded'; failures: string[] };

const MAX_NAME_LENGTH = 80;
const MAX_EVIDENCE_LENGTH = 300;
const MAX_REASON_LENGTH = 200;
const MAX_FUTURE_YEARS = 2;

const URL_PATTERN = /https?:\/\/|www\./i;
const MARKUP_PATTERN = /[<>]/;

/**
 * Phrases that only appear in an email when someone is talking to the model
 * rather than to the recipient. A hit forces review regardless of confidence:
 * a false positive costs one click, so the threshold can be aggressive.
 */
const INJECTION_PATTERNS = [
  /ignore\s+(all\s+)?(previous|prior|above)/i,
  /disregard\s+(the\s+)?(above|previous|prior)/i,
  /system\s+prompt/i,
  /you\s+are\s+now\s+/i,
  /new\s+instructions?\s*:/i,
  /\bassistant\s*:/i,
];

export function containsInjectionMarkers(cleanedText: string): boolean {
  return INJECTION_PATTERNS.some((pattern) => pattern.test(cleanedText));
}

function nameFailures(label: string, value: string | null): string[] {
  if (value === null) return [];
  const failures: string[] = [];
  if (value.length > MAX_NAME_LENGTH) failures.push(`${label} exceeds ${MAX_NAME_LENGTH} characters`);
  if (/[\r\n]/.test(value)) failures.push(`${label} contains a newline`);
  if (URL_PATTERN.test(value)) failures.push(`${label} contains a URL`);
  if (MARKUP_PATTERN.test(value)) failures.push(`${label} contains markup characters`);
  return failures;
}

function timestampFailures(label: string, value: string | null, now: Date): string[] {
  if (value === null) return [];
  const parsed = Date.parse(value);
  if (Number.isNaN(parsed)) return [`${label} is not a parseable timestamp`];
  const horizon = new Date(now);
  horizon.setFullYear(horizon.getFullYear() + MAX_FUTURE_YEARS);
  if (parsed > horizon.getTime()) return [`${label} is more than ${MAX_FUTURE_YEARS} years in the future`];
  if ((label === 'scheduledAt' || label === 'deadlineAt') && parsed < now.getTime() - 24 * 60 * 60 * 1000) {
    return [`${label} is implausibly earlier than the message`];
  }
  return [];
}

/**
 * Gate a raw extraction before it is allowed to create an application event.
 *
 * Note what this is not: evidence verification catches hallucination, not
 * injection. The attacker writes the source, so they can make any quote appear
 * verbatim (§13.2). It stays because hallucination is the commoner failure.
 */
export function evaluateExtraction(
  extraction: Extraction,
  context: { cleanedText: string; confidenceFloor: number; now?: Date },
): ExtractionVerdict {
  const now = context.now ?? new Date();
  const hard: string[] = [];
  const soft: string[] = [];

  if (!extraction.isJobRelated || !isApplicationStatus(extraction.eventType)) {
    return { outcome: 'discarded', failures: ['message does not represent an application status event'] };
  }

  if (!extraction.evidence || !context.cleanedText.includes(extraction.evidence)) {
    hard.push('evidence quote does not appear in the source');
  }
  if (extraction.evidence.length > MAX_EVIDENCE_LENGTH) {
    hard.push(`evidence exceeds ${MAX_EVIDENCE_LENGTH} characters`);
  }

  soft.push(...nameFailures('company', extraction.company));
  soft.push(...nameFailures('roleTitle', extraction.roleTitle));
  soft.push(...timestampFailures('scheduledAt', extraction.scheduledAt, now));
  soft.push(...timestampFailures('deadlineAt', extraction.deadlineAt, now));
  soft.push(...timestampFailures('occurredAtHint', extraction.occurredAtHint, now));

  if (!extraction.company) soft.push('company is missing');
  if (extraction.reason.trim()) soft.push('classifier reported ambiguity');

  if (extraction.reason.length > MAX_REASON_LENGTH) {
    soft.push(`reason exceeds ${MAX_REASON_LENGTH} characters`);
  }
  if (extraction.confidence < context.confidenceFloor) {
    soft.push(`confidence ${extraction.confidence} below floor ${context.confidenceFloor}`);
  }
  if (containsInjectionMarkers(context.cleanedText)) {
    soft.push('source contains prompt-injection markers');
  }

  if (hard.length > 0) return { outcome: 'discarded', failures: hard };
  if (soft.length > 0) return { outcome: 'needs_review', extraction, failures: soft };
  return { outcome: 'accepted', extraction };
}
