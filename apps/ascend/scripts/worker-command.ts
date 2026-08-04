import { safeOperationalError } from '@/security/safe-error';

export async function runWorkerCommand(name: string, operation: () => Promise<void>): Promise<void> {
  const startedAt = new Date();
  console.log(JSON.stringify({ event: 'worker.started', name, startedAt: startedAt.toISOString() }));

  try {
    await operation();
    console.log(JSON.stringify({ event: 'worker.finished', name, finishedAt: new Date().toISOString() }));
  } catch (error) {
    console.error(JSON.stringify({
      event: 'worker.failed',
      name,
      error: safeOperationalError(error),
    }));
    process.exitCode = 1;
  }
}
