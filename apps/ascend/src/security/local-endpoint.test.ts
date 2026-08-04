import { describe, expect, it } from 'vitest';
import { isLoopbackEndpoint, requireLoopbackEndpoint } from './local-endpoint';

describe('local Ollama boundary', () => {
  it('allows loopback HTTP endpoints', () => {
    expect(isLoopbackEndpoint('http://127.0.0.1:11434')).toBe(true);
    expect(isLoopbackEndpoint('http://localhost:11434')).toBe(true);
  });

  it('rejects remote, authenticated and non-HTTP endpoints', () => {
    expect(isLoopbackEndpoint('https://ollama.example.com')).toBe(false);
    expect(isLoopbackEndpoint('http://token@127.0.0.1:11434')).toBe(false);
    expect(isLoopbackEndpoint('https://127.0.0.1:11434')).toBe(false);
    expect(() => requireLoopbackEndpoint('https://ollama.example.com')).toThrow('loopback');
  });
});
