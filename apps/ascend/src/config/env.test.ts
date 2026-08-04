import { describe, expect, it } from 'vitest';

import { parseServerEnvironment } from './env';

describe('parseServerEnvironment', () => {
  it('accepts the required server configuration', () => {
    const result = parseServerEnvironment({
      APP_ENV: 'test',
      APP_ORIGIN: 'http://localhost:3000',
      DATABASE_URL: 'postgresql://localhost/ascend',
      CLOUDFLARE_ACCESS_TEAM_DOMAIN: 'example.cloudflareaccess.com',
      CLOUDFLARE_ACCESS_AUDIENCE: 'test-audience',
      CLOUDFLARE_TURNSTILE_SECRET_KEY: 'test-turnstile-secret',
      GOOGLE_CLIENT_ID: 'test-client',
      GOOGLE_CLIENT_SECRET: 'test-secret',
      GOOGLE_OAUTH_REDIRECT_URI: 'http://localhost:3000/api/v1/oauth/gmail/callback',
      TOKEN_ENCRYPTION_KEYS: '{"1":"dGVzdC10ZXN0LXRlc3QtdGVzdC10ZXN0LXRlc3QtdGVzdC10ZXM="}',
      INVITE_RATE_LIMIT_SECRET: 'test-rate-limit-secret',
      OLLAMA_BASE_URL: 'http://127.0.0.1:11434',
      OLLAMA_MODEL: 'qwen3:8b',
    });

    expect(result.APP_ENV).toBe('test');
    expect(result.OLLAMA_MODEL).toBe('qwen3:8b');
    expect(result.EXTRACTION_CONFIDENCE_FLOOR).toBe(0.7);
    expect(result.DEFAULT_TIMEZONE).toBe('Europe/London');
    expect(result.INVITE_SEAT_LIMIT).toBe(15);
  });
});
