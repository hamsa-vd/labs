import { describe, expect, it } from 'vitest';
import {
  applicationEventTypes,
  applicationRecordStatuses,
  applicationStatuses,
  terminalStatuses,
  type ApplicationRecordStatus,
} from './application-event';
import { applicationOrigins, applicationStage, applicationStages } from './application';

/**
 * WP1 Part B. `applications.current_status` can now hold `'draft'`. The column's
 * type widens; the projection's type must not. These two facts are tested
 * separately and on purpose — the second one is the security-relevant half.
 */

const projectableStatuses = [
  'applied',
  'acknowledged',
  'assessment',
  'interview_invite',
  'interview_scheduled',
  'offer',
  'rejected',
  'withdrawn',
] as const;

describe('applicationRecordStatuses', () => {
  it('admits draft', () => {
    expect(applicationRecordStatuses).toContain('draft');
  });

  it('admits every projectable status alongside draft', () => {
    for (const status of projectableStatuses) {
      expect(applicationRecordStatuses).toContain(status);
    }
  });

  it('is exactly draft prepended to applicationStatuses', () => {
    expect([...applicationRecordStatuses]).toEqual(['draft', ...applicationStatuses]);
  });

  it('has no member the database check constraint would reject', () => {
    expect(new Set(applicationRecordStatuses).size).toBe(applicationRecordStatuses.length);
    expect(applicationRecordStatuses).toHaveLength(projectableStatuses.length + 1);
  });

  it('types the column, so a draft value is assignable', () => {
    const columnValue: ApplicationRecordStatus = 'draft';
    expect(columnValue).toBe('draft');
  });
});

describe('applicationStatuses stays closed', () => {
  it('does NOT include draft', () => {
    expect(applicationStatuses).not.toContain('draft');
    expect((applicationStatuses as readonly string[]).includes('draft')).toBe(false);
  });

  it('is unchanged: the eight projectable statuses, in order', () => {
    expect([...applicationStatuses]).toEqual([...projectableStatuses]);
  });

  it('keeps the terminal set unchanged', () => {
    expect([...terminalStatuses]).toEqual(['offer', 'rejected', 'withdrawn']);
    expect(terminalStatuses).not.toContain('draft');
  });
});

describe('applicationEventTypes stays closed', () => {
  it('does NOT include draft, so no classifier and no projection can emit it', () => {
    expect(applicationEventTypes).not.toContain('draft');
    expect((applicationEventTypes as readonly string[]).includes('draft')).toBe(false);
  });

  it('is unchanged: the eleven v1 event types, in order', () => {
    expect([...applicationEventTypes]).toEqual([
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
    ]);
  });

  it('still contains every projectable status, so applicationStatuses remains a subset', () => {
    for (const status of applicationStatuses) {
      expect(applicationEventTypes).toContain(status);
    }
  });
});

describe('applicationStages', () => {
  it('starts with draft', () => {
    expect(applicationStages[0]).toBe('draft');
  });

  it('keeps the existing columns after draft, in order', () => {
    expect([...applicationStages]).toEqual([
      'draft',
      'applied',
      'acknowledged',
      'assessment',
      'interview',
      'offer',
    ]);
  });
});

describe('applicationStage', () => {
  it('maps draft to its own board column', () => {
    expect(applicationStage('draft')).toBe('draft');
  });

  it('still collapses the granular interview states', () => {
    expect(applicationStage('interview_invite')).toBe('interview');
    expect(applicationStage('interview_scheduled')).toBe('interview');
  });

  it('still keeps terminal closed states off the board', () => {
    expect(applicationStage('rejected')).toBeNull();
    expect(applicationStage('withdrawn')).toBeNull();
  });

  it('maps every non-terminal record status onto a declared stage', () => {
    for (const status of applicationRecordStatuses) {
      const stage = applicationStage(status);
      if (status === 'rejected' || status === 'withdrawn') {
        expect(stage).toBeNull();
        continue;
      }
      expect(stage).not.toBeNull();
      expect(applicationStages).toContain(stage);
    }
  });
});

describe('applicationOrigins', () => {
  it('includes generated and imported', () => {
    expect(applicationOrigins).toContain('generated');
    expect(applicationOrigins).toContain('imported');
  });

  it('keeps the existing origins', () => {
    expect(applicationOrigins).toContain('gmail');
    expect(applicationOrigins).toContain('manual');
  });

  it('is exactly the four origins the database check constraint allows', () => {
    expect([...applicationOrigins].sort()).toEqual(['generated', 'gmail', 'imported', 'manual']);
  });
});
