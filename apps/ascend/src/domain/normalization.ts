const LEGAL_SUFFIXES = /\b(?:ltd|limited|inc|llc|gmbh|plc|group|company|co)\b/gi;

export function normalizeEntity(value: string): string {
  return value.normalize('NFKC').toLowerCase().replace(LEGAL_SUFFIXES, '').replace(/[^\p{L}\p{N}]+/gu, ' ').trim().replace(/\s+/g, ' ');
}
