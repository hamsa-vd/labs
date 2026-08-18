const ATS_DOMAINS = new Map<string, string>([
  ['greenhouse.io', 'greenhouse'], ['my.greenhouse.io', 'greenhouse'],
  ['lever.co', 'lever'], ['hire.lever.co', 'lever'], ['ashbyhq.com', 'ashby'],
  ['myworkday.com', 'workday'], ['myworkdayjobs.com', 'workday'], ['icims.com', 'icims'],
  ['smartrecruiters.com', 'smartrecruiters'], ['workable.com', 'workable'],
  ['breezy.hr', 'breezy'],
  ['teamtailor.com', 'teamtailor'], ['jobvite.com', 'jobvite'], ['recruitee.com', 'recruitee'],
  ['personio.de', 'personio'], ['pinpointhq.com', 'pinpoint'], ['bamboohr.com', 'bamboohr'],
  ['successfactors.com', 'successfactors'], ['taleo.net', 'taleo'], ['avature.net', 'avature'],
  ['multiverse.io', 'multiverse'], ['multiverse.com', 'multiverse'],
]);

const AGGREGATORS = new Map<string, string>([
  ['linkedin.com', 'linkedin'], ['indeed.com', 'indeed'], ['otta.com', 'otta'],
  ['welcometothejungle.com', 'welcometothejungle'], ['glassdoor.com', 'glassdoor'],
  ['wellfound.com', 'wellfound'], ['hired.com', 'hired'], ['cord.co', 'cord'],
]);

const SUBJECT_PATTERNS = [
  /thank you for (?:applying|your (?:application|interest))/i,
  /application (?:received|status|update|submitted|progress|decision|outcome)/i,
  /(?:update|status|decision|outcome).{0,30}(?:your )?application/i,
  /we (?:regret|are unable)/i,
  /unfortunately|not moving forward|will not be progressing|other candidates|no longer under consideration/i,
  /moving forward|next steps/i,
  /\binterview\b|interview invitation|interview invite/i,
  /(?:technical|coding|online) assessment/i,
  /schedule.{0,20}(?:call|interview)|(?:call|interview).{0,20}(?:schedule|invite)/i,
  /offer of employment/i,
];

export interface PrefilterInput {
  fromAddress: string;
  subject: string;
  hasListUnsubscribe?: boolean;
  isCalendarAutoReply?: boolean;
}

export interface PrefilterResult {
  score: number;
  reasons: string[];
  shouldClassify: boolean;
  source: string;
  fromDomain: string;
}

export function senderDomain(address: string): string {
  return address.split('@').at(-1)?.trim().toLowerCase() ?? '';
}

function domainLookup(domain: string, values: Map<string, string>): string | null {
  for (const [candidate, source] of values) {
    if (domain === candidate || domain.endsWith(`.${candidate}`)) return source;
  }
  return null;
}

export function prefilterMessage(input: PrefilterInput): PrefilterResult {
  const fromDomain = senderDomain(input.fromAddress);
  const ats = domainLookup(fromDomain, ATS_DOMAINS);
  const aggregator = domainLookup(fromDomain, AGGREGATORS);
  const subjectMatch = SUBJECT_PATTERNS.some((pattern) => pattern.test(input.subject));
  const jobAlert = aggregator === 'linkedin' && /job alert|jobs for you|new jobs/i.test(input.subject);
  const hardNegative = input.isCalendarAutoReply || jobAlert || (input.hasListUnsubscribe && !ats && !subjectMatch);
  const reasons: string[] = [];
  let score = 0;

  if (ats) { score += 3; reasons.push(`ats:${ats}`); }
  if (subjectMatch) { score += 2; reasons.push('subject:job-pattern'); }
  if (aggregator) { score += 1; reasons.push(`aggregator:${aggregator}`); }
  if (hardNegative) { score = 0; reasons.push('hard-negative'); }

  return { score, reasons, shouldClassify: score >= 2, source: ats ?? aggregator ?? 'direct', fromDomain };
}
