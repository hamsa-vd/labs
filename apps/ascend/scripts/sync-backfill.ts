import { notImplemented, runWorkerCommand } from './worker-command';

await runWorkerCommand('sync.backfill', () => notImplemented('Gmail backfill'));
