import { database } from '@/infrastructure/database';
import { runWorkerCommand } from './worker-command';

await runWorkerCommand('persistence.audit', async () => {
  const forbiddenColumns = await database().query<{ table_name: string; column_name: string }>(
    `select table_name,column_name from information_schema.columns
     where table_schema='public'
       and (
         (table_name='raw_messages' and column_name ~* '(^|_)(body|body_html|body_text|model_input)($|_)')
         or column_name ~* '(^|_)(evidence_text|model_input)($|_)'
         or (table_name='llm_extractions' and column_name='evidence')
       )`,
  );
  const leakedEvidence = await database().query<{ count: string }>(
    `select count(*)::text from llm_extractions where output ? 'evidence'`,
  );
  const plaintextTokens = await database().query<{ table_name: string; column_name: string }>(
    `select table_name,column_name from information_schema.columns
     where table_schema='public' and column_name in ('refresh_token','access_token','gmail_token')`,
  );
  const findings = {
    forbiddenColumns: forbiddenColumns.rows,
    outputsContainingEvidence: Number(leakedEvidence.rows[0]?.count ?? 0),
    plaintextTokenColumns: plaintextTokens.rows,
  };
  console.log(JSON.stringify({ event: 'persistence.audit', ...findings }));
  if (findings.forbiddenColumns.length || findings.outputsContainingEvidence || findings.plaintextTokenColumns.length) {
    throw new Error('Persistence audit failed');
  }
});
