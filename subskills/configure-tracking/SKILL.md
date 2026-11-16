---
name: my-configure-tracking
description: Configure or reconcile my squad tracking in Onmove. Use for first setup, focus discovery, adding squads or projects, correcting source bindings, changing leads or cadence agreements, pausing/reactivating squads, and project handoffs.
---

# Configure squad tracking

Read [contracts](../../references/contracts.md) and the
[Onmove adapter](../../references/onmove-api.md). Use
[Focus Note](../../assets/templates/focus-note.md) and
[Squad Note](../../assets/templates/squad-note.md) templates as logical content.
Templates are not MCP payloads. Only the coordinator creates or edits Onmove objects;
a delegated configuration worker returns a ConfigurationProposal.

## Discover capabilities and the tracking home

1. Inspect exposed Onmove operations and schemas plus source read capabilities.
   Resolve tenant/workspace identity. Store connection aliases and stable IDs, never
   credentials. The local desktop MCP URL does not prove access from a cloud host.
2. Prefer an explicit binding from the request or a workspace instruction. Otherwise
   inspect Notes containing MY_SQUAD_TRACKING_V1, compact Focus inventory and
   exact likely titles including paused/closed lifecycles. Follow complete pagination.
3. Read candidate Notes and hierarchy. Match tracker_namespace, intended organization,
   Focus identity and schema. Use semantic search only to discover candidates.
4. With one verified match, store/reuse its returned IDs. With ambiguous matches,
   ask which tracker. With a known ID that is missing/inaccessible, ask about access
   or binding; do not create a replacement. With complete discovery finding no
   tracker and a setup request, create the Focus and initialize its Default Note.
5. Create/reuse a Team oversight Thread under that Focus and resolve its Default
   Note. Record both IDs in Focus configuration. Keep it outside the squad registry.
   Give its Note a concise purpose and pointer to the Focus Note; keep the portfolio
   checkpoint and pending write state in the Focus Note, not two competing copies.

Use the adapter's exact creation and Note revision rules. Re-read after ambiguous
creates and preserve verified IDs through partial setup. No create_note operation
exists in the verified adapter. Preserve human content outside managed blocks.

## Ask for the minimum useful configuration

Discover likely source candidates from explicitly supplied board/channel/repository/
page URLs or a bounded approved organization scope. Validate candidates by native IDs
and current content. Do not crawl all repositories, messages or people by default.

Ask in a small coherent batch for information that cannot be determined reliably:

- Which squads and exact Jira boards/filters define their work?
- Which Slack channels, GitHub repository/paths, and Confluence project roots or
  pinned pages belong to each squad?
- What outcomes, required working agreements and manager check-ins matter now?
- Which lead/ownership relationships and source mappings are uncertain?

A Jira board and stable squad identity permit partial setup. Other sources may be
unconfigured or unavailable with explicit coverage limitations. Do not call missing
connectors optional successes. Ask only the unresolved questions and proceed with
confirmed squads. Do not invent Capy, Paul, project names or organizational rules
from examples. Let the user refine richer configuration over subsequent runs.

## Focus configuration

Populate schema version, tracker namespace, exact Focus/Note IDs, timezone, oversight
binding, squad directory, shared policy/document registry, defaults and run budgets.
Use the configured marker for discovery. Keep any workspace bootstrap pointer small:
the main skill name plus explicit Focus/Note binding or tracker namespace is enough.

Prefer manual invocation and textual status. Set no schedule. Record configured
bootstrap lookback, overlap, reconciliation cadence, context budget and concurrency.
Keep defaults distinct from requirements. Store required policy with authority,
effective date, expected outcome, source, authorized exceptions and review trigger.

The Focus Note also holds current portfolio context, global unresolved decisions
and risks, due manager attention and the last accepted squad checkpoint references.
Do not duplicate every squad's detailed project state in it.

## Squad configuration and understanding the work

Assign a stable opaque squad_uid once; keep it across renames, staffing changes and
pauses. Bind it to a verified Onmove Thread and its Note and the Focus parent.
Maintain these distinct parts:

- **Identity/lifecycle:** current label, aliases, active/paused/retired periods,
  effective dates, reasons and next review.
- **Source bindings:** tenant, board ID and actual filter fingerprint, channel IDs,
  repository identities and path/branch scopes, Confluence page/space IDs.
- **People and responsibility:** dated role/membership intervals, confirmed lead,
  decision owner and assignment conventions. Name people only where operationally
  relevant. Unknown effective dates remain unknown.
- **Work/project registry:** stable project IDs, intended user/business outcome,
  scope and acceptance/Done conditions, Jira epic/work links, requirements/design/
  decision/rollout documents, dependencies, phases, rollout/maintenance obligations,
  and current/historical squad ownership.
- **Agreements:** required/default/squad-owned practices, cadence/timezones, intended
  outputs, local exceptions and evidence of authorization.
- **Observations:** dated patterns, counterexamples and uncertainty. Store these in
  checkpoint.observed_patterns, not as accepted policy.
- **Open work for the manager:** squad-level check-ins, coaching experiments, retro
  items, decisions and completion/review conditions.

A shared repository or board can cover multiple squads/projects. Record explicit
association rules, retain ambiguous items and ask; authorship alone is insufficient.
Pin older active project documents even when they lie outside the bootstrap window.

## Reconcile change over time

A human statement in the current request can authorize an update. Record its effective
date and provenance; ask only if ambiguity would materially affect ownership or work.

For a lead change, end the old interval and add the new one. Do not rewrite historical
attribution or assume every obligation transfers to the new lead. Flag handoffs that
need an owner. Reassignment of a Jira ticket is evidence of ticket ownership, not an
automatic squad membership or lead change.

For a project handoff, keep the work_uid and source IDs. Record both ownership
intervals, originating and destination squads and open handoff/release obligations.
Keep the originating squad's tombstone/pointer; establish new squad source coverage
without reusing an unrelated cursor. Shared obligations retain a canonical item ID.

For an explicitly requested rename or lifecycle change, reconcile both the tracker
configuration and Onmove Thread fields using the adapter. Verify each write; if only
one succeeds, preserve its result and report the remaining reconciliation. Internal
retired requires explicit done/cancelled disposition for an Onmove lifecycle change.

For pause, retain unresolved risks, decisions, check-ins and dates. Configure whether
to check open items only, continue selected sources, or wait for explicit reactivation.
Do not mark work complete or treat lack of commits as a pause request.

For reactivation, confirm current staffing and projects, reconcile membership and
watched work, inspect current source state, and backfill accessible changes since the
last complete coverage. If the gap exceeds budget/retention, record the gap and the
explicit current baseline; do not fabricate continuous history.

For a source/filter change, close the old scope with provenance and create/rebaseline
a new scope_fingerprint. Preserve old source_state and unresolved watchlist entries
until disposition is known. Do not move a coverage cursor into the new query scope.

## Return and persist

Return ConfigurationProposal with exact verified bindings, proposed configuration,
authority/provenance, unresolved questions, source availability and intended writes.
Separate discovered candidates from accepted mappings.

The coordinator validates and uses checkpoint-state for existing Note changes.
During first setup, initialize supported schema/identity and null coverage, using
revision-guarded writes. Record verified object IDs before continuing other creation.
Report partial setup precisely. A connector's existence is not proof of a successful
collection, and configuration alone is not an observed squad assessment.
