import {
  isApplicationStatus,
  isTerminalStatus,
  type ApplicationEvent,
  type ApplicationStatus,
} from './application-event';

/**
 * Derive an application's current status from its whole event history.
 *
 * Two obvious rules are both wrong (architecture §5):
 *
 *   - Highest rank wins pins an application at `offer` forever, even after you
 *     decline it, and cannot represent `rejected` sensibly at all.
 *   - Latest event wins breaks on out-of-order mail, dragging an application
 *     backwards when a delayed acknowledgement lands after an interview invite.
 *
 * The rule that survives both: order by occurredAt, take the latest, but never
 * regress out of a terminal state. Only another terminal event can change a
 * terminal one, which correctly handles rejected-after-offer and a role
 * reopening after a rejection.
 *
 * Pure and total, so it can be replayed over the full history after a prompt
 * version change without migrating anything.
 */
export function projectStatus(events: readonly ApplicationEvent[]): ApplicationStatus | null {
  const ordered = [...events]
    .filter((event) => isApplicationStatus(event.type))
    .sort((a, b) => {
      const byOccurred = a.occurredAt.getTime() - b.occurredAt.getTime();
      if (byOccurred !== 0) return byOccurred;
      // Same instant: manual corrections outrank model output.
      if (a.source !== b.source) return a.source === 'manual' ? 1 : -1;
      return a.createdAt.getTime() - b.createdAt.getTime();
    });

  let status: ApplicationStatus | null = null;

  for (const event of ordered) {
    const candidate = event.type as ApplicationStatus;

    if (status !== null && isTerminalStatus(status) && !isTerminalStatus(candidate)) {
      // A non-terminal event arriving after a conclusion is recorded in the
      // timeline but must not move the board.
      continue;
    }

    status = candidate;
  }

  return status;
}

/** The instant the projected status became true, for `status_as_of`. */
export function projectStatusAsOf(events: readonly ApplicationEvent[]): Date | null {
  const status = projectStatus(events);
  if (status === null) return null;

  const matching = events
    .filter((event) => event.type === status)
    .sort((a, b) => b.occurredAt.getTime() - a.occurredAt.getTime());

  return matching[0]?.occurredAt ?? null;
}
