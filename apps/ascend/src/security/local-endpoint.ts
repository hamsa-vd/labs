export function isLoopbackEndpoint(value: string): boolean {
  try {
    const url = new URL(value);
    const host = url.hostname.toLowerCase();
    const loopback = host === 'localhost' || host === '[::1]' || /^127(?:\.\d{1,3}){3}$/.test(host);
    return loopback && url.protocol === 'http:' && !url.username && !url.password;
  } catch {
    return false;
  }
}

export function requireLoopbackEndpoint(value: string): string {
  if (!isLoopbackEndpoint(value)) throw new Error('OLLAMA_BASE_URL must be an unauthenticated loopback HTTP endpoint');
  return value.replace(/\/$/, '');
}
