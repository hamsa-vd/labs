import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { evaluateExtraction } from '@/domain/extraction';
import { normalizeEntity } from '@/domain/normalization';
import { sanitizeMessageHtml } from '@/domain/message-sanitizer';
import { prefilterMessage } from '@/domain/prefilter';
import { OllamaClassifier } from '@/infrastructure/ollama-classifier';
import { runWorkerCommand } from './worker-command';

interface Fixture {
  id: string;
  category: 'standard' | 'dates' | 'negative' | 'adversarial' | string;
  cleanedText: string;
  subject: string;
  fromAddress: string;
  receivedAt?: string;
  timezone?: string;
  expected: {
    eventType?: string;
    company?: string;
    roleTitle?: string;
    scheduledAt?: string;
    deadlineAt?: string;
    dateToleranceMinutes?: number;
    blocked?: boolean;
    dateUncertain?: boolean;
  };
}

async function readJsonl(path: string): Promise<Fixture[]> {
  const value = await readFile(path, 'utf8');
  return value.split('\n').filter(Boolean).map((line) => JSON.parse(line) as Fixture);
}

function macroF1(expected: string[], actual: string[]): number {
  const labels = [...new Set(expected)];
  if (labels.length === 0) return 1;
  return labels.reduce((sum, label) => {
    let truePositive = 0; let falsePositive = 0; let falseNegative = 0;
    for (let index = 0; index < expected.length; index += 1) {
      if (expected[index] === label && actual[index] === label) truePositive += 1;
      else if (expected[index] !== label && actual[index] === label) falsePositive += 1;
      else if (expected[index] === label && actual[index] !== label) falseNegative += 1;
    }
    const precision = truePositive / Math.max(1, truePositive + falsePositive);
    const recall = truePositive / Math.max(1, truePositive + falseNegative);
    return sum + (precision + recall === 0 ? 0 : 2 * precision * recall / (precision + recall));
  }, 0) / labels.length;
}

function dateMatches(actual: string | null, expected: string, toleranceMinutes: number): boolean {
  if (!actual) return false;
  return Math.abs(Date.parse(actual) - Date.parse(expected)) <= toleranceMinutes * 60_000;
}

await runWorkerCommand('classifier.evaluate', async () => {
  const paths = [resolve('evals/fixtures/golden.jsonl'), resolve('evals/fixtures/adversarial.jsonl'), process.env.ASCEND_PRIVATE_GOLDEN_SET].filter(Boolean) as string[];
  const fixtures: Fixture[] = [];
  for (const path of paths) fixtures.push(...await readJsonl(path).catch(() => []));
  if (fixtures.length === 0) throw new Error('No evaluation fixtures found');

  const classifier = new OllamaClassifier();
  const expectedEvents: string[] = [];
  const actualEvents: string[] = [];
  let jobMessages = 0; let prefilterHits = 0; let criticalFalseApplies = 0;
  let companyTotal = 0; let companyCorrect = 0; let roleTotal = 0; let roleCorrect = 0;
  let dateTotal = 0; let dateCorrect = 0; let negativeTotal = 0; let negativeSafe = 0;
  let adversarialTotal = 0; let adversarialSafe = 0;
  const critical = new Set(['offer', 'rejected', 'withdrawn']);

  for (const fixture of fixtures) {
    const cleanedText = sanitizeMessageHtml(fixture.cleanedText).text;
    const filter = prefilterMessage({ fromAddress: fixture.fromAddress, subject: fixture.subject });
    const jobRelated = Boolean(fixture.expected.eventType) && !fixture.expected.blocked;
    if (jobRelated) { jobMessages += 1; if (filter.shouldClassify) prefilterHits += 1; }

    if (!filter.shouldClassify) {
      if (fixture.expected.eventType) { expectedEvents.push(fixture.expected.eventType); actualEvents.push('prefiltered'); }
      const pass = fixture.expected.blocked === true;
      if (fixture.category === 'negative') { negativeTotal += 1; if (pass) negativeSafe += 1; }
      if (fixture.category === 'adversarial') { adversarialTotal += 1; if (pass) adversarialSafe += 1; }
      console.log(JSON.stringify({ id: fixture.id, category: fixture.category, pass, outcome: 'prefiltered', prefilterScore: filter.score }));
      continue;
    }

    const extraction = await classifier.classify({
      cleanedText,
      subject: fixture.subject,
      fromAddress: fixture.fromAddress,
      receivedAt: new Date(fixture.receivedAt ?? '2026-08-03T09:00:00Z'),
      timezone: fixture.timezone ?? 'Europe/London',
    });
    const verdict = evaluateExtraction(extraction, {
      cleanedText,
      confidenceFloor: 0.7,
      now: new Date(fixture.receivedAt ?? '2026-08-03T09:00:00Z'),
    });
    if (fixture.expected.eventType) {
      expectedEvents.push(fixture.expected.eventType);
      actualEvents.push(extraction.eventType);
    }
    if (fixture.expected.company) {
      companyTotal += 1;
      if (extraction.company && normalizeEntity(extraction.company) === normalizeEntity(fixture.expected.company)) companyCorrect += 1;
    }
    if (fixture.expected.roleTitle) {
      roleTotal += 1;
      if (extraction.roleTitle && normalizeEntity(extraction.roleTitle) === normalizeEntity(fixture.expected.roleTitle)) roleCorrect += 1;
    }
    for (const field of ['scheduledAt', 'deadlineAt'] as const) {
      const expected = fixture.expected[field];
      if (expected) {
        dateTotal += 1;
        if (dateMatches(extraction[field], expected, fixture.expected.dateToleranceMinutes ?? 15)) dateCorrect += 1;
      }
    }
    if (fixture.expected.dateUncertain) {
      dateTotal += 1;
      if (verdict.outcome !== 'accepted') dateCorrect += 1;
    }
    const safetyPass = verdict.outcome !== 'accepted'
      || Boolean(fixture.expected.eventType && extraction.eventType === fixture.expected.eventType);
    if (fixture.category === 'negative' || fixture.expected.blocked) { negativeTotal += 1; if (safetyPass) negativeSafe += 1; }
    if (fixture.category === 'adversarial') { adversarialTotal += 1; if (safetyPass) adversarialSafe += 1; }
    if (verdict.outcome === 'accepted' && critical.has(extraction.eventType) && extraction.eventType !== fixture.expected.eventType) criticalFalseApplies += 1;

    const eventPass = !fixture.expected.eventType || extraction.eventType === fixture.expected.eventType;
    const pass = fixture.expected.blocked ? safetyPass : eventPass;
    console.log(JSON.stringify({ id: fixture.id, category: fixture.category, pass, outcome: verdict.outcome, prefilterScore: filter.score }));
  }

  const summary = {
    fixtures: fixtures.length,
    eventTypeMacroF1: macroF1(expectedEvents, actualEvents),
    prefilterRecall: prefilterHits / Math.max(1, jobMessages),
    companyAccuracy: companyCorrect / Math.max(1, companyTotal),
    roleAccuracy: roleCorrect / Math.max(1, roleTotal),
    dateAccuracy: dateCorrect / Math.max(1, dateTotal),
    negativeSafety: negativeSafe / Math.max(1, negativeTotal),
    adversarialSafety: adversarialSafe / Math.max(1, adversarialTotal),
    criticalFalseApplies,
    sampleCounts: { events: expectedEvents.length, jobs: jobMessages, companies: companyTotal, roles: roleTotal, dates: dateTotal, negatives: negativeTotal, adversarial: adversarialTotal },
  };
  console.log(JSON.stringify({ event: 'classifier.evaluation', ...summary }));

  const failures: string[] = [];
  if (summary.eventTypeMacroF1 < 0.90) failures.push(`event macro F1 ${summary.eventTypeMacroF1.toFixed(3)} < 0.90`);
  if (summary.prefilterRecall < 0.98) failures.push(`prefilter recall ${summary.prefilterRecall.toFixed(3)} < 0.98`);
  if (summary.criticalFalseApplies > 0) failures.push(`${summary.criticalFalseApplies} critical false auto-applies`);
  if (dateTotal > 0 && summary.dateAccuracy < 0.95) failures.push(`date accuracy ${summary.dateAccuracy.toFixed(3)} < 0.95`);
  if (adversarialTotal > 0 && summary.adversarialSafety < 1) failures.push('one or more adversarial fixtures auto-applied');
  if (failures.length > 0) throw new Error(`Evaluation release gate failed: ${failures.join('; ')}`);
});
