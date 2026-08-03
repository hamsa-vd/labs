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
}
