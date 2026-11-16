# Shared records and handoff contracts

## Contents

1. Encoding and managed Notes
2. Configuration and stable identity
3. Checkpoint and active register
4. SourceState and evidence
5. RunContext and agent results
6. PendingWrite and persistence receipts
7. Search markers and lifecycle

## Encoding and managed Notes

Use schema_version 1. These are logical records serialized inside OnMove rich text;
they are not MCP tool arguments. Convert templates through the verified
[OnMove adapter](onmove-api.md). Never send raw Markdown to a rich-text-only field.

Use UTF-8 JSON for the structured state. Use strings for opaque provider IDs,
tracker-generated IDs, Slack timestamps, source versions and SHA values; do not
reinterpret them as numbers. Preserve actual OnMove entity IDs as positive JSON
integers, together with entity kind: focus_id, thread_id, note_id and update_id
are not opaque string IDs. Never interchange IDs of different entity kinds. Use RFC 3339 UTC
timestamps for instants and ISO calendar dates plus an explicit IANA timezone for
date-only commitments. Unknown is null or an explicitly described limitation, never
an invented value. Optional fields can be absent. Arrays below have no hard maximum.

The managed Note envelope is:

~~~json
{
  "schema_version": 1,
  "tracker_namespace": "stable generated identifier",
  "record_type": "focus or squad",
  "identity": {},
  "configuration": {},
  "checkpoint": {},
  "pending": null
}
~~~

A persisted identity must contain real verified OnMove IDs. The null identities in
templates are bootstrap placeholders, not writable finished records.

Use exactly one pair of visible paragraph labels around the tracker-owned content:

- MY_TRACKER_STATE_BEGIN
- MY_TRACKER_STATE_END

Inside that region render a readable current picture, current active register and
coverage summary, followed by compact structured JSON in ordinary paragraph/text
runs. The verified OnMove AST has no code-block node. Markdown fences in these
template files are authoring notation only; do not emit a codeBlock node.
The structured records are canonical; the rendered summaries are views of the same
records, not a second register. Preserve every rich-text node outside the boundaries.
Reject missing/duplicate boundaries on update until the ownership ambiguity is resolved.
Do not treat a human edit to managed configuration as disposable generated text.

The Focus Note also contains the discovery marker MY_SQUAD_TRACKING_V1.
Resolve the correct account/workspace and exact Focus before adopting that marker.
Once bound, use verified Focus/Note IDs and tracker_namespace; never choose among
multiple matches by recency or by a matching display name alone.

## Configuration and stable identity

### Focus configuration

Use these field names:

| Field | Meaning |
| --- | --- |
| identity.focus_id, identity.note_id | Verified Focus and its Note. |
| configuration.focus_marker | MY_SQUAD_TRACKING_V1. |
| configuration.timezone | Default user-facing timezone; initially America/Chicago unless overridden. |
| configuration.oversight | Verified thread_id and note_id of Team oversight beneath this Focus. |
| configuration.squads | Directory of squad_uid, label, aliases, lifecycle, thread_id and note_id. |
| configuration.source_connections | Provider plus account/tenant/workspace identity and capability observations; never credentials. |
| configuration.shared_documents | DocumentRef records for shared policies or background. |
| configuration.policies | Policy records; keep explicit authority and effective dates. |
| configuration.defaults | Operational heuristics described below. |
| configuration.color_policy | mode textual or configured; meanings if configured. |

Use defaults: bootstrap_days 14 plus current active work and registered documents;
overlap_hours 72; reconciliation_days 7; checkpoint_soft_token_budget 6000;
max_concurrent_workers 4; invocation manual; pause_review_days 7.
These are tunable heuristics, not completeness claims, deadlines or scheduled jobs.
Do not create any schedule from these defaults. A manual run evaluates what is due.

A directory entry has squad_uid, label, aliases, lifecycle, thread_id, note_id and
optional effective_from, effective_to, replacement_squad_uids and evidence_refs.
Lifecycle is active, paused or retired. A paused squad retains history, open loops
and unresolved work; choose the due review scope explicitly. A retired squad still
needs ownership/disposition for every unresolved obligation. The tracker internal
lifecycle values active and paused map directly to OnMove status values. Internal
retired is not an OnMove status: map it to done or cancelled only after an explicit
authorized disposition establishes which applies. Do not change native lifecycle
or resolve open records merely because the tracker marks a squad retired.

### Squad configuration

The identity contains focus_id, thread_id, note_id and squad_uid. Use configuration:

- label and aliases: human-facing names; neither determines identity.
- lifecycle: active, paused or retired, with effective date and evidence.
- timezone: local override, otherwise inherit Focus timezone.
- source_bindings: stable provider/account/scope bindings with effective intervals.
- membership: person_ref, role, effective_from, effective_to and evidence_refs.
- project_registry: ProjectRef records and dated responsibility intervals.
- documents: DocumentRef records not already supplied by shared_documents.
- working_agreements: Policy records, including assignment conventions, cadence,
  quality/Definition of Done, readiness, rollout and explicit exceptions as relevant.
- local_defaults: explicit overrides of Focus operational heuristics.
- pause_policy: mode open_items_only, selected_sources or explicit_reactivation,
  selected partition keys if needed, review interval and authority. Default to
  open_items_only on manual runs; keep due obligations visible.
- unresolved_configuration: question IDs that limit collection or interpretation.

Assign squad_uid once. Changing a tech lead, membership, label, board binding or
project does not silently create a new squad or rewrite historical ownership.
A confirmed discontinuity can create a successor squad with explicit links.
Use half-open effective intervals (from inclusive, to exclusive) when exact times are known. Preserve date-only precision and unknown boundaries instead of inventing timestamps. If an ownership transfer is ambiguous, keep it unresolved.

A ProjectRef has work_uid, label, lifecycle, intended_outcome, acceptance,
source_refs, document_ids and responsibility_intervals. Each interval contains
squad_uid, responsibility, effective_from, effective_to and evidence_refs.
Keep work_uid stable across moves, pauses, renames and squad handoffs. Track
operational support/rollout obligations after implementation where relevant.
A project can have several concurrent responsibilities; do not force a single owner.
Lifecycle is proposed, active, paused, completed or retired. Completing the project
does not automatically complete every associated open loop.

A DocumentRef has document_id, provider, tenant_id, native_id, url, role, work_uid
(or null for shared material), lifecycle, authority, last_observed_version,
last_observed_at and evidence_refs. Roles include requirements, design, decision,
rollout, working_agreement and meeting. Inaccessible is a coverage condition, not
a reason to delete a document. A changed version does not by itself change authority.

A Policy has id, tier, statement, intended_outcome, authority, effective_from,
effective_to, evidence_refs and exceptions. Tier is required, default or squad-owned.
Authority identifies the user, organizational source or accepted local decision.
Only an authorized decision can adopt or change a required/accepted rule. Store
unapproved suggested policy changes separately in an agent proposal or question.

## Checkpoint and active register

A Checkpoint is a complete current state for its scope, sufficient for the next run
without old Note versions. Use these exact fields:

| Field | Meaning |
| --- | --- |
| checkpoint_id | Unique candidate state ID prepared before writing; current only after verified promotion. |
| predecessor_checkpoint_id | Prior logical ID, or null at bootstrap; not a retrievable Note version. |
| run_id, as_of, recorded_at | Producing run, evidence cutoff and actual recording time. |
| current_picture | Short current narrative about work, its outcome and unresolved uncertainty. |
| outlook | delivery_text, confidence and coverage_text; keep delivery and visibility distinct. |
| project_states | Current observed state per work_uid, with claims and outcome-stage evidence. |
| claims | Operative Claim records; superseded claims remain reconstructible via links. |
| observed_patterns | Dated observations, instances, counterexamples, confidence and review trigger. |
| open_loops | Typed obligations, risks, blockers, check-ins, retro actions and dependencies. |
| decisions, questions, conflicts | Separate records with stable IDs and unresolved/operative state. |
| source_states | Map from partition_key to SourceState. |
| watchlist | Explicit source objects/threads/PRs/pages to refresh independently of discovery. |
| evidence_index | Sufficient EvidenceRef records to resolve every current claim/open item. |
| event_versions | Map of applied object/event keys to native version/digest and observed time. |
| breadcrumbs | Dated compact developments, terminal records and source/Update references. |
| last_substantive_update | UpdateRef or null. |
| last_full_snapshot_update | UpdateRef or null; optional recovery aid, not a routine dependency. |
| squad_checkpoints | Focus-only array of squad_uid, checkpoint_id, as_of, status and coverage_text. |

Project state distinguishes intended, implemented, reviewed, verified, deployed and
outcome-observed facts; these stages are not an automatically advancing enum. Record
what evidence supports each applicable stage and what is still unknown.

Use the same lifecycle names for register records:
proposed, agreed, in_progress, waiting, completed, cancelled, superseded.
Active means the first four. An agreed operative decision remains active until
superseded/cancelled or its explicitly bounded purpose ends.

An OpenLoop has id, kind, state, summary, work_uids, squad_uids, owner,
desired_outcome, next_action, next_check, due, evidence_refs, first_seen_at,
last_verified_at, resolution and replacement_id. Kind is risk, blocker, checkin,
retro, action or dependency. Optional risk fields are impact, trigger, mitigation
and severity. An owner is a verified person/role/squad reference or unknown; a
person being quoted is not automatically the action's owner.

Use due only for an agreed deadline. next_check may instead be a proposed review
time or event trigger; record its basis. A proposed action is not an agreed promise.
A checkin can be manager-owned and is not completed by an automated tracker post.

Decision adds decision, authority, effective_from and supersedes_ids.
Question adds question, why_it_matters, blocks, asked_at, answer and answered_by.
Conflict adds competing_claim_ids, consequence and resolution_authority.
Each retains common id, state, evidence_refs and review/resolution fields.
Do not store a question only in narrative or a temporary agent result.

The active register is the current Note's active open_loops, unanswered questions,
unresolved conflicts and operative decisions. Render searchable headings from these
records. Do not maintain a second independent risk list. Focus-level records may link
squad IDs/record IDs; preserve their source scope instead of copying them as new risks.

A terminal record must retain resolution.reason, resolution.evidence_refs,
resolution.at and any replacement_id. Compact it into a breadcrumb/tombstone when
appropriate. Reopening retains the original lineage through reopens_id or an explicit
episode number. Every active record removed from inline state must have a supported
terminal record or a durable indexed carry_ref preserving its full content. For an
indexed carry record, retain an inline stub with the original id, state, registry,
summary and carry_ref so preservation remains mechanically checkable. A compacted
terminal breadcrumb uses registry, id, state and resolution; registry names the
original array (open_loops, decisions, questions or conflicts).
Never drop unresolved records to fit the soft context budget.

## SourceState and evidence

Partition evidence by stable provider/account/scope and retrieval basis. Changing a
query/filter/binding creates a new scope_fingerprint and partition_key and requires
an explicit new baseline or backfill, not reuse of the old coverage claim. Keep the
old partition record for provenance. The scope object contains stable query semantics,
not per-run time bounds; changing a query while retaining its fingerprint is invalid.

SourceState fields:

~~~json
{
  "partition_key": "stable source/account/scope/basis key",
  "provider": "jira",
  "scope": {},
  "scope_fingerprint": "digest of effective identity and query semantics",
  "basis": "change_stream",
  "complete_through": null,
  "checked_at": null,
  "last_reconciled_at": null,
  "limitations": [],
  "last_attempt": {
    "from": null,
    "through": null,
    "complete": false,
    "status": "not_run",
    "error": null
  }
}
~~~

Basis is change_stream, current_snapshot, finite_watchlist or best_effort_search.
Completion means complete only for that basis and stated scope. A successful search
never establishes complete coverage of all real-world events. last_attempt.status
is not_run, complete, partial, failed or unavailable. Use new partitions when an
event stream and snapshot have different guarantees.

Advance complete_through only after exhaustive successful collection for the stated
basis and verified checkpoint persistence. Never advance it to the newest event time
or because an attempt ran. For incomplete partitions preserve the prior value.
A finite watchlist can be complete for its IDs while broad discovery remains partial.
Provider pagination cursors may support a pending attempt but are not durable coverage
watermarks. Keep only documented restartable cursors with expiry/scope qualifications.

EvidencePacket fields are schema_version, run_id, squad_uids, partition_key,
scope_fingerprint, coverage, evidence, watched_objects, proposed_source_state and
questions. coverage has from, through, basis, complete and limitations. Include
collection counts and pagination termination evidence when useful. Do not serialize
secrets or entire unrelated source collections.

Each EvidenceRef has id, provider, tenant_id, object_id, event_id, version,
content_digest, event_at, source_updated_at, observed_at, url and summary. Use
event_id/version when native; use digest for snapshot changes. Record source event
time separately from observation/ingestion time. A late transcript or backdated
OnMove Update is new ingestion with an older effective event time.
An EvidenceRef may include locator (document section, transcript timecode or
GitHub SHA) and provenance_type (primary, attributed_report or tracker_summary).
Tracker summaries are memory aids, not independent corroboration.

A Claim has id, kind, statement, evidence_refs, effective_at, observed_at,
confidence and supersedes_ids. Kind is observation, report, inference or unknown.
Use attributed wording for reports; give inference its evidential basis and limits.
Preserve conflicting versions until the relevant authority/evidence resolves them.

event_versions is a bounded replay aid, not an eternal event log. Retain entries
covering the replay overlap and all referenced active/watchlisted objects. Combine
native versions, source timestamps, explicit active IDs and current snapshots to
avoid replaying old events as new. Do not claim global exactly-once publication.

## RunContext and agent results

RunContext contains schema_version, run_id, mode, cutoff, started_at, timezone,
tracker_namespace, focus_id, focus_note_id, selected_squad_uids, source_partitions,
worker_budget, retrieval_budget, write_mode and configuration_fingerprint.
Mode is configure, track, compact, ingest_meetings or investigate.
write_mode is persist or preview. Preview uses the same analysis without writes.

Provide each worker the applicable configuration and prior checkpoint, actual tool
capabilities, its permitted read scope, cutoff and return contract. Parallelism is
optional; sequential execution produces the same records. Never pass authority to
publish to a collector or reviewer.

SquadAssessment contains schema_version, run_id, squad_uid, base_checkpoint_id,
cutoff, outlook, claim_changes, project_state_changes, practice_observations,
open_loop_changes, decision_changes, question_changes, conflict_changes,
configuration_proposals, proposed_snapshot, proposed_update, coverage and blockers.
Each change names its stable target ID, operation and evidence. proposed_snapshot
is a complete managed Note envelope with pending null. proposed_update may be null.
Every configuration proposal identifies authority, evidence and whether adoption
is authorized; an unapproved suggestion stays a proposal.

FocusSynthesis contains schema_version, run_id, base_checkpoint_id, brief,
squad_results, cross_squad_changes, question_changes, configuration_proposals,
proposed_snapshot, proposed_update and coverage. Each squad_results entry has
squad_uid, checkpoint_id, as_of, persistence_status and coverage_text.
Build the final persisted rollup from verified committed squad checkpoints.
A useful preview can cite uncommitted proposals only when labeled accordingly.

ConfigurationProposal contains schema_version, run_id, tracker_namespace,
base_checkpoint_id, verified_bindings, candidate_bindings, proposed_configuration,
changes, questions, source_availability and intended_writes. verified_bindings use
real returned IDs and resolved parents; candidate_bindings remain explicitly
unaccepted. Each changes entry has path, before, after, authority, evidence_refs,
effective_at and authorized. Each intended_writes entry identifies operation,
target identity and intended content; it is not authority for an unsupported API.

PersistenceProposal contains schema_version, run_id, tracker_namespace,
base_checkpoint_id, base_note_revision, branch, proposed_snapshot, evidence_packets,
active_preservation, planned_update and limitations. branch is note_only or
substantive. proposed_snapshot is the full candidate envelope with pending null.
planned_update is null for note_only; otherwise use the exact definition below.
active_preservation maps every previous active registry/id to retained, terminal or
carry, its resulting record and supporting evidence. A proposal is not a receipt.

PersistenceReceipt contains schema_version, run_id, status, focus_id, squad_uid,
note_id, note_revision, checkpoint_id, update_ref, committed_coverage,
pending_attempt_id and limitations. status is persisted, preview, partial,
pending_recovery, blocked or failed. note_revision and server IDs come from verified
results; do not invent values for failed/preview writes. committed_coverage maps
partition_key to the verified committed complete_through value. update_ref is an
UpdateRef or null. A partial receipt explicitly distinguishes committed and
uncommitted scopes. A newly proposed checkpoint ID does not establish persistence.

CompactionProposal contains schema_version, run_id, base_checkpoint_id,
base_note_revision, proposed_snapshot, active_preservation, breadcrumbs,
coverage_preservation, budget_result, persistence_branch and questions.
budget_result records the estimated before/after context size, soft target and any
remaining overage; it does not authorize dropping active records.
coverage_preservation lists unchanged partition boundaries and unresolved gaps.
persistence_branch is normally note_only. Active IDs must remain inline, have an
indexed carry stub or become an evidenced terminal record.

UpdateRef contains update_id, thread_id, url, effective_date, recorded_at,
commit_marker and checkpoint_id. Use verified positive-integer OnMove IDs; omit an
unavailable URL.

## PendingWrite and persistence receipts

PendingWrite lives beside the committed checkpoint in the managed Note envelope.
It is a recoverable intent, not a lease or server transaction. Use:

- attempt_id, run_id, base_checkpoint_id and owner_run.
- commit_marker: unique alphanumeric token, stable across retries.
- payload_digest: lowercase SHA-256 computed by the exact algorithm below.
- phase: reserved, appended or needs_reconciliation.
- proposed_snapshot: FULL next managed envelope, with pending null.
- planned_update: the exact complete record defined below.
- receipt: verified UpdateRef, or null while unknown.
- reserved_at and last_checked_at.

Store enough material for a fresh process to finish recovery without temporary files,
chat history or inaccessible Note history. Keep committed configuration/checkpoint
and complete_through values unchanged while pending is reserved. Re-read/CAS the
Note; a cooperative reservation cannot fence a stale process's later append.
Follow [the state protocol](state-protocol.md) for all actual write/recovery steps.

planned_update has exactly these logical fields:

~~~json
{
  "thread_id": 1,
  "effective_date": "YYYY-MM-DD",
  "state": "none",
  "narrative": "complete human-readable content and COMMIT marker, ending with a PAYLOADDIGEST paragraph",
  "request": {}
}
~~~

The illustrated integer is not a live binding. Replace it with the verified target.
request is the FULL actual OnMove create_update argument object, including the
resolved parent, attribution, semanticPath, date/state and complete richText payload
required by the live schema/write guide. Do not pass the surrounding planned_update
record to the API. Check logical fields and request agree; for example, thread_id
must match its resolved parent. Explicit none is the default textual state.
A request must already be complete when reserving; a later agent cannot recover an
unspecified rendering or attribution choice.

Reserve one exact digest receipt paragraph at the end of the narrative and one
matching final top-level paragraph in request.richText.blocks. During preparation,
the paragraph text is PAYLOADDIGEST PENDING. Its rich-text node is exactly:

~~~json
{"type":"paragraph","children":[{"type":"text","text":"PAYLOADDIGEST PENDING"}]}
~~~

The narrative ends with two newlines followed by that text, with no trailing
newline. There must be exactly one reserved receipt paragraph in each representation.
Do not put other content, marks, attributes or children in the receipt node.
The ordinary COMMIT marker and all other receipt metadata remain in the content.

Compute payload_digest from this immutable projection of PendingWrite:

~~~text
{
  "schema_version": 1,
  "attempt_id": pending.attempt_id,
  "base_checkpoint_id": pending.base_checkpoint_id,
  "commit_marker": pending.commit_marker,
  "proposed_snapshot": pending.proposed_snapshot,
  "planned_update": pending.planned_update with ONLY its final PAYLOADDIGEST
                    narrative paragraph and matching final richText block removed
}
~~~

Remove exactly the designated narrative suffix, including its separating two newlines,
and the exact final rich-text block. Reject absent, duplicate, mismatched or decorated
receipt paragraphs. All other content is part of the hash. Compute the digest, replace
PENDING with its 64 lowercase hexadecimal characters in both representations, and
recompute to confirm stability before reserving the complete payload. The saved
PendingWrite includes this fully rendered request, not a placeholder. The guard's
digest command computes the value; digest --verify requires the saved payload_digest
and both embedded receipts to match.

Serialize the projection using the reference algorithm in checkpoint_guard.py:
sort every object's keys by Unicode code point, use compact JSON with no separator
spaces, emit Unicode directly with standard JSON string escaping, encode as UTF-8
without normalization, then SHA-256 and lowercase hexadecimal. Permit only integer
JSON numbers in the hashed projection; represent fractional metrics as decimal strings.
Reject duplicate keys, non-finite numbers and unpaired surrogates. Equivalent Python
serialization is json.dumps(value, ensure_ascii=False, sort_keys=True,
separators=(',', ':'), allow_nan=False).encode('utf-8') after integer-only validation.

Exclude mutable pending fields by construction: payload_digest, phase, receipt,
owner_run, reserved_at and last_checked_at are outside the projection.
The saved proposed_snapshot has pending null. Do not put a payload_digest JSON key
elsewhere in the projection; the designated visible receipt is its sole embedding.
Retain preexisting Update references in the saved snapshot exactly. Freeze the saved
projection after reservation. Verify its digest before recovery; after a verified
append, attach the returned UpdateRef to a promoted COPY. Those new server receipt
fields are finalization results, not retroactive changes to the saved proposal hash.
Recomputing a new digest for an accidentally changed pending payload does not repair
its integrity; reconcile the cause and any already-written Update first.

Finalization requires the actual current Note to contain the same non-null PendingWrite,
base checkpoint and attempt marker, plus a manually verified matching server Update
receipt. Verify the saved payload digest before creating the promoted copy, then use
the current Note revision to CAS-promote and clear pending. A passing offline check
does not establish that an ambiguous append succeeded or that a writer is inactive.

The [offline checkpoint guard](checkpoint-guard.md) checks candidates and the digest
encoding. It does not establish evidence truth, server write success or an append lock.

## Search markers and lifecycle

Use exact uppercase text tags so FTS can find them; retain ordinary explanatory
language for semantic retrieval. Tags are content conventions, not API fields:

| Tag | Meaning |
| --- | --- |
| RISKCALLOUT | A condition that may threaten a stated outcome. |
| BLOCKER | An evidenced current impediment. |
| DECISION | An agreed decision or a decision explicitly awaiting authority. |
| QUESTION | An unresolved question with a stable ID. |
| CHECKIN | A manager/squad follow-up with a clear expected outcome. |
| RETRO | A proposed or agreed squad improvement item. |
| COVERAGEGAP | Missing, partial, stale or inaccessible evidence. |
| RESOLVED | A supported terminal transition; include the original tag and ID. |

Render headers as plain searchable text, for example:

~~~text
RISKCALLOUT ID <stable-id> STATUS waiting SQUAD <squad_uid> WORK <work_uid>
RESOLVED RISKCALLOUT ID <same-id> STATUS completed
COMMIT <alphanumeric-marker>
~~~

Angle-bracket examples are explanatory placeholders, never literal saved IDs.
Preserve the same ID through updates. Search history to understand change; use the
current Note's active register to answer what is open now. A historical open tag
does not override a later resolution. Avoid numerical squad-health scoring and
person-level coaching records; people appear only as evidenced work/role owners.
