---
name: my-compact-memory
description: Compact squad-tracking state while preserving unresolved work, evidence, source coverage, and recovery information. Use when a squad checkpoint or recent history exceeds its context budget, at a configured review point, or when explicitly asked to compact tracking memory.
---

# Compact squad memory

Read the coordinator's [SKILL.md](../../SKILL.md), the
[state protocol](../../references/state-protocol.md), and the
[OnMove adapter](../../references/onmove-api.md). Use the coordinator's effective
configuration and state schema. Return a proposal; only the coordinator writes.

## Inputs

Require the current supported checkpoint, lossless Note content/revision, applicable
global and squad settings, active-register IDs, source coverage, recent receipts,
and the intended context budget. Request missing inputs from the coordinator.
Do not load an entire Thread history just to compact its current state.

Stop the affected proposal if the checkpoint schema or rich-text version is newer
than supported. Recover or preserve pending state before compaction; do not erase
an incomplete write to simplify the Note.

## Preserve the operational meaning

Separate stable settings from changing context. Keep approved cadence/practice
agreements distinct from observed variations, inferred patterns, and coaching ideas.
Preserve current project/document references, source bindings, and effective dates.
Do not promote repeated mistakes into approved practices during summarization.

Build a short current picture that answers:

- What outcome is this squad pursuing, and what evidence shows its present state?
- What changed materially, and what uncertainty remains?
- Which next actions belong to the manager, squad, or another dependency owner?
- What should the next run check, and when?

Keep every proposed, agreed, in_progress, or waiting open loop. Preserve its stable
ID, owner/unknown, dates, evidence, and next-check trigger. Retain unanswered questions,
unresolved contradictions, operative decisions, and meaningful negative evidence.
Absence of recent mentions does not resolve an item. An automated summary does not
complete a human check-in.

## Compress only what can be reconstructed

Merge repeated narrative into a current conclusion with the smallest sufficient
evidence set. Preserve factual provenance and uncertainty; do not preserve private
chain of thought. Replace duplicated raw excerpts with concise paraphrases and links.

Summarize closed developments into dated breadcrumbs. For completed, cancelled, or
superseded items retain the closure basis and replacement/reopening relationship.
Use a logical tombstone rather than deleting history. Keep a pointer to older evidence
only when it can answer a concrete future question; never require its routine reread.

Preserve source_states, including complete_through, checked_at, scope/query identity,
collection limitations, and failures. Do not advance a cursor merely because its
history was summarized. Do not collapse independently incomplete sources into one
optimistic last-checked timestamp.

Retain the most recent substantive Update and full-snapshot references when present.
A predecessor checkpoint ID is a breadcrumb, not a guarantee that Note history can
be fetched. Ensure the new Note remains self-contained without historical Note APIs.

## Check preservation before handing back

Produce a before/after map for every active item, unanswered question, unresolved
contradiction, and operative decision. Each must remain present or have a supported
resolution or explicit durable carry-record reference. Reject silent truncation,
including truncation to satisfy a schema array limit or token target.

If active state is too large, propose indexed carry records or a specific scope split
and list the items needing user triage. Mark the compaction incomplete until no active
item would be lost. A smaller summary is not a success if it hides obligations.

Keep unresolved evidence conflicts legible. A later planning document does not prove
that implementation changed; a merged PR does not prove release or user adoption.

## Return contract

Return these explicit sections to the coordinator:

1. Proposed managed snapshot and its supported schema version.
2. Preserved active IDs and any justified resolution/replacement mappings.
3. Closed-history breadcrumbs with source/Update references.
4. Source-coverage preservation check and unresolved collection limitations.
5. Context-budget result, remaining overage, and targeted questions if needed.
6. Persistence recommendation and the base checkpoint/revision used.

Recommend the note-only expectedRevision CAS path for pure compaction. Preserve all
human-owned rich-text nodes. OnMove Update posts affect display state and review
freshness, so do not request a technical checkpoint post or history deletion.
When a useful substantive synthesis is independently due, the coordinator may include
a full snapshot in that narrative Update using the pending/append/finalize protocol.

If the Note changes before persistence, require reread and reconciliation. Never
overwrite a newer checkpoint, silently discard a human correction, or clear a pending
attempt belonging to a potentially active writer.
