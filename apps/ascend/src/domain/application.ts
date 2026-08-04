import type { ApplicationStatus } from './application-event';

export interface Application {
  id: string;
  userId: string;
  companyNormalized: string;
  companyDisplay: string;
  roleTitle: string | null;
  /**
   * Normalised role, part of the entity-resolution key. Company alone is not
   * enough: one company routinely runs two concurrent applications, and
   * matching on company only silently merges them. See architecture §5.
   */
  roleNormalized: string | null;
  /** Derived from the sender domain at prefilter time, never from the model. */
  source: string | null;
  firstSeenAt: Date;
  /** A projection over application_events, not an authoritative field. */
  currentStatus: ApplicationStatus;
  statusAsOf: Date;
  archived: boolean;
  origin: ApplicationOrigin;
  jobUrl: string | null;
  note: string | null;
}

export const applicationOrigins = ['gmail', 'manual'] as const;
export type ApplicationOrigin = (typeof applicationOrigins)[number];

export const applicationStages = ['applied', 'acknowledged', 'assessment', 'interview', 'offer'] as const;
export type ApplicationStage = (typeof applicationStages)[number];

export function applicationStage(status: ApplicationStatus): ApplicationStage | null {
  if (status === 'interview_invite' || status === 'interview_scheduled') return 'interview';
  if (status === 'rejected' || status === 'withdrawn') return null;
  return status;
}
