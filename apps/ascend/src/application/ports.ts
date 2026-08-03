import type { Application } from '@/domain/application';
import type { ApplicationEvent } from '@/domain/application-event';
import type { Extraction } from '@/domain/extraction';

export interface ApplicationRepository {
  findByUser(userId: string): Promise<Application[]>;
  findById(userId: string, applicationId: string): Promise<Application | null>;
}

export interface ApplicationEventRepository {
  append(event: ApplicationEvent): Promise<void>;
  findByApplication(applicationId: string): Promise<ApplicationEvent[]>;
}

export interface GmailMessageSource {
  backfill(accountId: string): Promise<void>;
  /**
   * A stale historyId returns HTTP 404 and the only recovery is a full resync.
   * Implementations must handle that path, not just the happy one: a home Mac
   * Mini offline for a week guarantees it. See architecture §4.2.
   */
  syncIncremental(accountId: string): Promise<void>;
}

/**
 * Strips HTML to text and removes anything the recipient could not see:
 * display:none and visibility:hidden elements, white-on-white text, comments,
 * style and script blocks, zero-width and bidi control characters. This is a
 * security control, not only a quality one, because hidden instructions are how
 * injection arrives in HTML mail. See architecture §13.3.
 */
export interface MessageSanitizer {
  clean(html: string): string;
}

export interface ClassificationRequest {
  cleanedText: string;
  subject: string;
  fromAddress: string;
  /** Anchor for resolving relative dates such as "within 5 days of this link". */
  receivedAt: Date;
  timezone: string;
}

export interface MessageClassifier {
  classify(request: ClassificationRequest): Promise<Extraction>;
}

/**
 * Generates the overview headline. Deliberately takes structured rows rather
 * than message text: this output is rendered in the most trusted position on
 * the page, so nothing an attacker wrote may reach it. See architecture §13.1.
 */
export interface DigestGenerator {
  generate(input: {
    userId: string;
    since: Date;
    events: readonly ApplicationEvent[];
    applications: readonly Application[];
  }): Promise<{ headline: string; body: string; fallbackUsed: boolean }>;
}
