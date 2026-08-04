export type AccessAllowlistStatus = 'active' | 'revoked';

export interface AccessAllowlistEntry {
  id: string;
  email: string;
  status: AccessAllowlistStatus;
  note: string | null;
  addedAt: Date;
  revokedAt: Date | null;
}

export type SyncJobStatus = 'queued' | 'running' | 'completed' | 'failed';

export interface SyncJob {
  id: string;
  accountId: string;
  requestedBy: string | null;
  mode: 'incremental' | 'full';
  status: SyncJobStatus;
  messagesScanned: number;
  candidatesFound: number;
  eventsCreated: number;
  requestedAt: Date;
  startedAt: Date | null;
  finishedAt: Date | null;
  error: string | null;
}
