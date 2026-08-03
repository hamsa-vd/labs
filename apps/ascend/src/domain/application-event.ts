/**
 * What the classifier may emit. A closed enum, so no prompt injection can
 * invent a new one (architecture §13.1).
 */
export const applicationEventTypes = [
  'applied',
  'acknowledged',
  'assessment',
  'interview_invite',
  'interview_scheduled',
  'offer',
  'rejected',
  'withdrawn',
  'recruiter_outreach',
  'job_alert',
  'other',
] as const;

export type ApplicationEventType = (typeof applicationEventTypes)[number];

/**
 * What an application's status may be. A strict subset of the event types:
 * `recruiter_outreach`, `job_alert` and `other` are things that happen to an
 * inbox, not states an application can be in.
 */
export const applicationStatuses = [
  'applied',
  'acknowledged',
  'assessment',
  'interview_invite',
  'interview_scheduled',
  'offer',
  'rejected',
  'withdrawn',
] as const;

export type ApplicationStatus = (typeof applicationStatuses)[number];

/**
 * Once an application reaches one of these, a later non-terminal event must not
 * drag it backwards. Out-of-order mail is normal: a delayed "we have received
 * your application" often lands after an interview invite. See §5.
 */
export const terminalStatuses = ['offer', 'rejected', 'withdrawn'] as const;

export type TerminalStatus = (typeof terminalStatuses)[number];

export function isApplicationStatus(value: ApplicationEventType): value is ApplicationStatus {
  return (applicationStatuses as readonly string[]).includes(value);
}

export function isTerminalStatus(value: ApplicationStatus): boolean {
  return (terminalStatuses as readonly string[]).includes(value);
}

/**
 * Statuses shown as board columns. Rejected and withdrawn leave the board and
 * remain visible in the table and timeline (§11.4).
 */
export const boardColumnStatuses = [
  'applied',
  'acknowledged',
  'assessment',
  'interview_invite',
  'interview_scheduled',
  'offer',
] as const;

export type ApplicationEventSource = 'llm' | 'manual';

export interface ApplicationEvent {
  id: string;
  applicationId: string;
  rawMessageId: string | null;
  type: ApplicationEventType;
  /** When the event happened, not when it was ingested. */
  occurredAt: Date;
  /** Interview or call booking, resolved to an instant. See §11.3.2. */
  scheduledAt: Date | null;
  /** Assessment or offer-response deadline, resolved to an instant. */
  deadlineAt: Date | null;
  source: ApplicationEventSource;
  createdAt: Date;
}
