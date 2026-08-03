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
      message: error instanceof Error ? error.message : String(error),
    }));
    process.exitCode = 1;
  }
}

export function notImplemented(name: string): Promise<void> {
  return Promise.reject(new Error(`${name} is scaffolded but not implemented`));
}
