import { describe, expect, it } from 'vitest';
import { applicationStage } from './application';
import { normalizeEntity } from './normalization';

describe('applicationStage', () => {
  it('maps granular interview states into one board column', () => {
    expect(applicationStage('interview_invite')).toBe('interview');
    expect(applicationStage('interview_scheduled')).toBe('interview');
  });
  it('keeps terminal closed states off the board', () => {
    expect(applicationStage('rejected')).toBeNull();
    expect(applicationStage('withdrawn')).toBeNull();
  });
});

describe('normalizeEntity', () => {
  it('removes legal suffixes without merging the role', () => {
    expect(normalizeEntity('Monzo Bank Ltd.')).toBe('monzo bank');
    expect(normalizeEntity('Senior Front-end Engineer')).toBe('senior front end engineer');
  });
});
