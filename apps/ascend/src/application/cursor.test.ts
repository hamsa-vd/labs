import { randomUUID } from 'node:crypto';
import { describe, expect, it } from 'vitest';
import { decodeCursor, encodeCursor } from './cursor';

describe('opaque list cursors', () => {
  it('round-trips a stable timestamp and id', () => {
    const at = new Date('2026-08-03T10:30:00.000Z');
    const id = randomUUID();
    expect(decodeCursor(encodeCursor(at, id))).toEqual({ at, id });
  });

  it('rejects malformed cursors', () => {
    expect(() => decodeCursor('not-a-cursor')).toThrow('invalid_cursor');
  });
});
