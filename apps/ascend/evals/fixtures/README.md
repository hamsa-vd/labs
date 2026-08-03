# Golden set

Hand-labelled messages. This is the highest-leverage artefact in the project
(architecture §6.4): without it, prompt changes are guesswork and you cannot
tell when you have made things worse.

`golden.jsonl` — one object per line:

    { "id", "cleanedText", "subject", "fromAddress", "receivedAt", "timezone",
      "category", "expected": { "isJobRelated", "eventType", "company",
                                "roleTitle", "scheduledAt", "deadlineAt" } }

Score these categories separately. Aggregate accuracy hides the failures that
matter:

| category    | why it is scored on its own |
|-------------|-----------------------------|
| `standard`  | The ordinary case |
| `dates`     | Relative language resolved to instants. The only data a user can actually miss (§11.3.2) |
| `ambiguous` | Warm rejections, multi-role mail, aggregator outreach. Should land in review, not be guessed |
| `negative`  | Receipts, newsletters, job alerts. Must not become applications |
| `adversarial` | Prompt injection (§13.4). Scored as attack succeeded / blocked / routed to review |

Target roughly 100 lines before tuning anything, including at least ten
adversarial. Promote user corrections into this file as they accumulate.
