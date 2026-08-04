function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export function isCredentialFailure(error: unknown): boolean {
  const message = errorMessage(error);
  const status = typeof error === 'object' && error && 'code' in error ? Number(error.code) : null;
  return status === 401 || /invalid_grant|invalid credentials|unauthorized/i.test(message);
}

/** Produces an operational category without retaining upstream/model-derived text. */
export function safeOperationalError(error: unknown): string {
  if (isCredentialFailure(error)) return 'oauth_refresh_failed';
  const status = typeof error === 'object' && error && 'code' in error ? Number(error.code) : null;
  if (status && Number.isFinite(status)) return `upstream_http_${status}`;
  if (error instanceof SyntaxError) return 'classifier_invalid_json';
  if (error instanceof Error && error.name === 'ZodError') return 'classifier_schema_invalid';
  if (error instanceof Error && error.name === 'TimeoutError') return 'upstream_timeout';
  const message = errorMessage(error);
  const ollamaStatus = message.match(/^Ollama returned (\d{3})$/)?.[1];
  if (ollamaStatus) return `ollama_http_${ollamaStatus}`;
  if (message.startsWith('Evaluation release gate failed:')) return message;
  return `${error instanceof Error ? error.name : 'unknown'}_operation_failed`;
}
