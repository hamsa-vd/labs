import { Badge } from '@labs/design/arey';
import type { ApplicationStatus } from '@/domain/application-event';

const labels: Record<ApplicationStatus,string> = { applied:'Applied',acknowledged:'Acknowledged',assessment:'Assessment',interview_invite:'Interview',interview_scheduled:'Interview',offer:'Offer',rejected:'Rejected',withdrawn:'Withdrawn' };
export function StatusBadge({ status }: { status: ApplicationStatus }) {
  const tone = status === 'offer' ? 'success' : status === 'rejected' || status === 'withdrawn' ? 'danger' : status.startsWith('interview') ? 'accent' : status === 'assessment' ? 'warning' : 'neutral';
  return <Badge tone={tone} dot>{labels[status]}</Badge>;
}
