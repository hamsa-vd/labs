import { runWorkerCycle } from '@/application/sync-service';
import { runWorkerCommand } from './worker-command';

await runWorkerCommand('sync.incremental', async () => {
  const processed = await runWorkerCycle();
  console.log(JSON.stringify({ event: 'worker.cycle', processed }));
  if (process.env.HEALTHCHECK_URL) await fetch(process.env.HEALTHCHECK_URL, { method: 'POST' });
});
