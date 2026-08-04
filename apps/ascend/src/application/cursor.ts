import { z } from 'zod';

const cursorSchema = z.object({ at: z.iso.datetime(), id: z.uuid() });

export interface PageCursor { at: Date; id: string }

export function encodeCursor(at: Date, id: string): string {
  return Buffer.from(JSON.stringify({ at: at.toISOString(), id }), 'utf8').toString('base64url');
}

export function decodeCursor(value: string | null | undefined): PageCursor | null {
  if (!value) return null;
  try {
    const parsed = cursorSchema.parse(JSON.parse(Buffer.from(value, 'base64url').toString('utf8')));
    return { at: new Date(parsed.at), id: parsed.id };
  } catch {
    throw new Error('invalid_cursor');
  }
}
