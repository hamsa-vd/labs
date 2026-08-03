import { z } from 'zod';

const serverEnvironmentSchema = z.object({
  APP_ENV: z.enum(['development', 'test', 'production']).default('development'),
  APP_ORIGIN: z.url(),
  DATABASE_URL: z.string().min(1),
  SUPABASE_SERVICE_ROLE_KEY: z.string().min(1),
  CLOUDFLARE_ACCESS_TEAM_DOMAIN: z.string().min(1),
  CLOUDFLARE_ACCESS_AUDIENCE: z.string().min(1),
  CLOUDFLARE_TURNSTILE_SECRET_KEY: z.string().min(1),
  GOOGLE_CLIENT_ID: z.string().min(1),
  GOOGLE_CLIENT_SECRET: z.string().min(1),
  GOOGLE_OAUTH_REDIRECT_URI: z.url(),
  TOKEN_ENCRYPTION_KEY: z.string().min(1),
  OLLAMA_BASE_URL: z.url().default('http://127.0.0.1:11434'),
  OLLAMA_MODEL: z.string().default('qwen3:8b'),
  PROMPT_VERSION: z.coerce.number().int().positive().default(1),
  EXTRACTION_CONFIDENCE_FLOOR: z.coerce.number().min(0).max(1).default(0.7),
  DEFAULT_TIMEZONE: z.string().min(1).default('Europe/London'),
  INVITE_SEAT_LIMIT: z.coerce.number().int().positive().default(15),
});

export type ServerEnvironment = z.infer<typeof serverEnvironmentSchema>;

export function parseServerEnvironment(
  environment: Record<string, string | undefined> = process.env,
): ServerEnvironment {
  return serverEnvironmentSchema.parse(environment);
}
