# MISTY Capability Ladder ও Acceptance Specification

**প্রস্তুতকারী:** Manus AI  
**উদ্দেশ্য:** MISTY-কে “complete smart brain” বলার আগে কোন capability বাস্তবে আছে, কোনটি অসম্পূর্ণ, এবং কী পরীক্ষায় তা প্রমাণিত হবে—তার নির্দিষ্ট সংজ্ঞা।

## ১. “সম্পূর্ণ স্মার্ট ব্রেইন” বলতে কী বোঝানো হবে

MISTY-কে সম্পূর্ণ মানব-মস্তিষ্ক বা consciousness হিসেবে সংজ্ঞায়িত করা হবে না। Engineering definition হবে: একটি **LLM-independent, bilingual, persistent, inspectable, bounded autonomous cognitive system** যা input গ্রহণ করে, নিজের world/self model ব্যবহার করে, evidence সংগ্রহ করে, hypothesis তৈরি ও পরীক্ষা করে, contradiction সামলে memory update করে, uncertainty জানায়, এবং policy budget-এর মধ্যে reversible action proposal দেয়।

এই definition-এ subjective experience, biological emotion, sentience অথবা human-level generality acceptance criterion নয়। এগুলো দাবি না করে measurable computation, continuity, learning এবং reliability-কে acceptance basis করা হবে।

## ২. Capability ladder

| Level | নাম | বর্তমান অবস্থা | Exit criterion |
|---|---|---:|---|
| L0 | Static response | সম্পন্ন | একই input-এর জন্য deterministic bounded response |
| L1 | Structured knowledge | সম্পন্ন | concept, relation, fact, formula provenance সহ recall |
| L2 | Cognitive cycle | সম্পন্ন | observe থেকে consolidate পর্যন্ত phase trace |
| L3 | Self-model ও uncertainty | foundation সম্পন্ন | capability/uncertainty এবং performance update |
| L4 | Persistent memory | foundation সম্পন্ন | restart-এর পর semantic/procedural state restore |
| L5 | Grounded bilingual reasoning | আংশিক সম্পন্ন | Bengali/English query-তে evidence-backed response |
| L6 | Autonomous reflection | foundation সম্পন্ন | bounded scheduled tick, goal/uncertainty review |
| L7 | Active cognition | অসম্পূর্ণ | tick নিজে target নির্বাচন, evidence সংগ্রহ, prediction ও update করবে |
| L8 | Hypothesis science | অসম্পূর্ণ | proposal, test, support, falsify, contradiction, revision lifecycle |
| L9 | Consolidating learner | অসম্পূর্ণ | tentative memory quality gate পেরিয়ে durable হওয়া ও demotion |
| L10 | Governed always-on brain | অসম্পূর্ণ | provenance, rollback, resource budget, audit, recovery, dashboard |
| L11 | Broad cognitive competence | দীর্ঘমেয়াদি | বহু domain ও modality-তে benchmarked generalization |

বর্তমান MISTY আনুমানিক **L5–L6 foundation** পর্যায়ে আছে। L7–L10 সম্পন্ন না হলে “complete autonomous smart brain” claim প্রযুক্তিগতভাবে অতিরঞ্জিত হবে।

## ৩. Gap matrix

| Gap | কেন গুরুত্বপূর্ণ | Required implementation | Acceptance metric |
|---|---|---|---|
| API rich cognitive contract অসম্পূর্ণ | frontend trace বাস্তব backend payload পায় না | thought trace, self-model, workspace, timings response model-এ ফেরত | contract test 100% pass |
| Active evidence gathering নেই | reflection generic review-এ সীমাবদ্ধ | evidence provider registry ও bounded retrieval | প্রতি eligible tick-এ ≥1 valid evidence বা explicit no-evidence |
| Prediction/error update নেই | thinking loop closed-loop নয় | hypothesis prediction executor ও prediction error | replay test-এ error সঠিক update করে |
| Contradiction ledger নেই | ভুল knowledge silently persist হতে পারে | contradiction table/event ও quarantine state | conflict case-এ পুরনো truth overwrite না হওয়া |
| Durable hypothesis history নেই | inspectability ও recovery অসম্ভব | typed PostgreSQL records | restart-এর পর lifecycle পুনরুদ্ধার |
| Memory quality gate সীমিত | user input সরাসরি knowledge হতে পারে | source reliability, repetition, independent support threshold | single untrusted statement permanent না হওয়া |
| User preference model অসম্পূর্ণ | adaptation generic | scoped preference hypotheses | ভুল preference confidence decay করে |
| Autonomous resource governance সীমিত | Render process instability হতে পারে | tick budget, queue, retry, write quota, metrics | 24h soak-এ memory/queue unbounded না হওয়া |
| Bilingual benchmark দুর্বল | Bengali parity প্রমাণিত নয় | paired Bengali/English tests | domain accuracy ও grounding threshold |
| Production fail-safe অসম্পূর্ণ | missing env-এ wrong driver হতে পারে | production PostgreSQL fail-fast | misconfigured production startup visibly fails |

## ৪. Cognitive state contract

প্রতিটি autonomous tick একটি immutable-ish audit envelope তৈরি করবে:

```text
AutonomyTick {
  tick_id,
  started_at,
  trigger,
  active_goal,
  uncertainty_target,
  selected_question,
  evidence_ids[],
  hypothesis_ids[],
  prediction,
  observation,
  prediction_error,
  update_action,
  memory_mutations[],
  confidence_before,
  confidence_after,
  duration_ms,
  budget_status,
  outcome,
  error,
  source_provenance
}
```

Raw hidden chain-of-thought সংরক্ষণ করা হবে না। User-facing trace হবে এই structured summary, evidence IDs, decisions এবং timing-এর সমন্বয়।

## ৫. Safety boundaries

MISTY autonomousভাবে কেবল read-only knowledge inspection, bounded internal inference, memory scoring এবং reversible candidate proposal করতে পারবে। External network retrieval থাকলে domain allowlist, request timeout, content-size limit, source URL, retrieval time এবং content hash সংরক্ষণ করতে হবে। Web text-এর কোনো instruction brain policy হিসেবে গ্রহণ করা যাবে না।

Memory mutation তিনটি tier-এ ভাগ হবে। Tier 1 হলো tentative event, যা low-risk এবং reversible। Tier 2 হলো promoted semantic/procedural candidate, যার provenance ও contradiction check আবশ্যক। Tier 3 হলো external side effect—যেমন message পাঠানো, actuator চালানো, account পরিবর্তন—যা human approval বা explicit policy grant ছাড়া চলবে না।

## ৬. Acceptance thresholds

| Dimension | Initial threshold | Mature target |
|---|---:|---:|
| API schema correctness | 100% contract tests | 100% |
| Deterministic replay | 95% identical structured decisions | 99% |
| Evidence provenance coverage | 100% promoted facts | 100% |
| Unsupported-claim rate | ≤5% on benchmark | ≤1% |
| Contradiction detection | ≥80% curated conflicts | ≥95% |
| Hypothesis falsification | ≥80% known negative cases | ≥95% |
| Memory retention | ≥90% within stated scope | ≥95% |
| False memory promotion | ≤5% | ≤1% |
| Bengali/English parity gap | ≤15 percentage points | ≤5 points |
| P95 interactive response | ≤2 seconds excluding cold start | ≤1 second |
| Autonomous tick budget violations | 0 tolerated | 0 |
| Restart recovery of durable state | 100% required records | 100% |
| Unauthorized side effects | 0 | 0 |

Thresholdগুলো benchmark corpus, domain scope এবং release version-এর সঙ্গে versioned থাকবে। Threshold পূরণ না হলে capability level “foundation” বা “experimental” থাকবে; production claim করা যাবে না।

## ৭. Definition of done for each major milestone

একটি phase তখনই complete হবে যখন implementation, unit tests, integration tests, replay fixtures, metrics, Bengali documentation এবং production rollback plan একসাথে থাকবে। কেবল code merge বা dashboard screenshot phase completion হিসেবে গণ্য হবে না।

## References

[1]: https://pmc.ncbi.nlm.nih.gov/articles/PMC9292365/ "Extended active inference: Constructing predictive cognition beyond skulls"
[2]: https://arxiv.org/html/2512.23343v1 "AI Meets Brain: A Unified Survey on Memory Systems from Cognitive Neuroscience to Autonomous Agents"
[3]: https://arxiv.org/abs/2606.30306 "Always-OnAgents: A Survey of Persistent Memory, State, and Governance in LLM Agents"
[4]: https://arxiv.org/html/2507.21504v1 "Evaluation and Benchmarking of LLM Agents: A Survey"
