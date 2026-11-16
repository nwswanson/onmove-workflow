---
name: my-checkpoint-state
description: Persist or recover validated Onmove squad-tracking state. Use only in the coordinator for Note checkpoints, substantive squad or oversight updates, configuration transitions, compaction and recovery from ambiguous or interrupted writes.
---

# Persist tracking state

Read [contracts](../../references/contracts.md), the entire
[state protocol](../../references/state-protocol.md), and the
[Onmove adapter](../../references/onmove-api.md) before a write.
Use the supported Onmove schemas, not conceptual fields as tool parameters.

This subskill is coordinator-only. A worker may prepare a PersistenceProposal or
inspect receipts read-only; it must never execute the write. Preview mode returns
the same concrete proposal and makes no changes.

## Preconditions

Require exact Focus/Thread/Note identities, current supported managed snapshot,
lossless Note rich text and revision, validated proposed snapshot, source receipts,
active-item preservation map and, if posting, the complete human-readable Update.

Resolve the actual write target and attribution with the current Onmove write guide.
Never assume an unscoped Subject. Verify every selected parent remains under the
configured Focus. For portfolio posts, reserve state in the Focus Note and append
to its configured Team oversight Thread.

Preserve human rich-text nodes. Readable Markdown is not a lossless round-trip format.
Serialize managed state inside supported paragraph/text nodes bounded by the agreed
visible labels. Reject missing/duplicate/conflicting managed boundaries or unsupported
versions. Do not silently replace the entire Note with a fresh template.

Check proposed source advances against their individual complete receipts, scope
and cutoff. Preserve unresolved open_loops, questions, conflicts, operative decisions
and pending data. Use [checkpoint_guard.py](../../scripts/checkpoint_guard.py) when
available; see its [limits](../../references/checkpoint-guard.md). Evidence truth,
policy authority and rich-text preservation still require coordinator validation.

## Recover before doing new work

If pending exists, establish whether the original writer is still active. A timestamp
is not a lease. Serialize complete runs; do not clear pending merely to proceed.

Use the saved marker, target, payload and full proposed snapshot. After an ambiguous
append, exhaust scoped literal search with all lifecycles, hydrate candidates and
compare exact marker, parent and semantic body. Do not filter by effective date.

One exact match permits recovery/finalization. Identical duplicates are recorded and
applied once logically; never auto-delete them. Conflicting branches, incomplete
search, uncertain absence or uncertain writer ownership keep pending and require a
targeted resolution. Continue other independent squads.

Do not retry a timed-out create_update on the assumption it failed. There is no
server append idempotency key or multi-operation transaction in the verified API.

## Choose the persistence branch

### Note-only checkpoint

Use for quiet runs, collection attempts/coverage changes, pure compaction or technical
state. Create a new self-contained checkpoint ID and predecessor link. Reread the
Note, reconcile relevant changes, and replace only managed blocks using expectedRevision.
Verify the returned/read-back checkpoint. After a timeout, read to establish the
result; never overwrite a newer checkpoint to make this run look successful.

### Substantive Update plus checkpoint

Use only for a meaningful change or useful periodic synthesis. Lead its narrative
with findings, implications, open risks/questions and next checks. Add compact
operational receipts after the useful content.

1. Prepare the full candidate snapshot with pending:null and the full complete
   planned_update. Give it a stable alphanumeric commit_marker, attempt_id, base
   checkpoint, and payload_digest following the exact contract. End narrative and
   richText with the designated PAYLOADDIGEST PENDING paragraph, compute the digest,
   then replace both final receipts with PAYLOADDIGEST plus the digest. Preserve the
   saved pre-receipt candidate; attach server UpdateRef only to the promoted copy.
2. Reread/reconcile the Note. CAS-reserve PendingWrite while retaining the committed
   checkpoint and its complete_through values unchanged. Save the FULL candidate
   and planned Update, including resolved target/date/state, so a fresh run can recover.
3. Verify the reservation. Append exactly the saved complete Update with the visible
   marker/receipt using the verified Onmove schema and current write guide.
4. Verify the returned Update's ID, parent, marker and semantic body. Ambiguous
   results enter recovery without advancing cursors.
5. Reread the Note; require the same pending attempt/base. Preserve human edits.
   For managed changes, follow the state protocol's recovery_rebase path: verify the
   original immutable proposal, compute a successor under current authorized context,
   and preserve a breadcrumb without pretending the old digest covers new content.
   CAS-promote the validated candidate/successor, attach the verified receipt, clear
   the matching pending attempt, and verify the final checkpoint.

Default textual state uses the explicit supported value none. Omission does not
preserve an old color. Follow actual configured color meanings if enabled. Do not
create technical heartbeat Updates: posts affect Onmove display/review freshness.

## Completion and failure reporting

Return a PersistenceReceipt with status, checkpoint ID, Note revision, Update ID if
any, coverage committed by partition, pending attempt if unresolved, and limitations.
Report collection, analysis and persistence separately.

A failed squad write cannot appear as committed in the Focus rollup. Use its prior
committed checkpoint with stale/blocked qualification and list unpersisted proposed
changes separately if useful. A Focus write failure does not undo already verified
squad writes; report that partial outcome explicitly.

Never delete Updates for compaction, silently rewrite historical conclusions, use
clear:true, or rely on Note-history access. Correct a substantive conclusion with
a visible supported correction and preserve its evidence trail.
