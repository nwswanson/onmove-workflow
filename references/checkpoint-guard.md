# Offline checkpoint guard

Use [checkpoint_guard.py](../scripts/checkpoint_guard.py) as an optional deterministic
check of the logical contracts. It uses only Python's standard library and has no
connector access, network calls or write operations. Other harnesses can follow the
same checks manually. Python is not required to run the skill workflow.

## Scope and limits

The guard checks fully bound candidate Note envelopes and a pre-reservation transition
from one committed checkpoint to its proposed successor. Both inputs must have
pending null. Use it before reserving a substantive write or replacing a quiet-run
checkpoint. Templates with unresolved null identities intentionally fail.

The guard does not validate a reservation or finalize a pending write. Preserve any
actual live pending record and use the state protocol to recover it. Finalization
requires the actual current Note to retain the matching PendingWrite and base,
a verified matching server Update receipt, a digest check of the immutable saved
proposal, and revision-guarded promotion of a copy. Do not mutate the saved proposal
with new server Update IDs before verifying its digest.

These checks cannot establish evidence truth, policy authority, correct source
membership, actual query pagination, server write success, ownership of a running
writer, full OnMove rich-text validity, or preservation of human rich-text nodes.
The digest command checks only its strict receipt-node convention and payload
integrity; it is not an API-request validator or a proof that a post exists.

## Commands

Run from the skill directory, or use the script's absolute path:

~~~sh
python3 scripts/checkpoint_guard.py validate candidate.json
python3 scripts/checkpoint_guard.py transition previous.json candidate.json --packets packets.json --cutoff 2026-11-16T17:00:00Z
python3 scripts/checkpoint_guard.py digest pending.json
python3 scripts/checkpoint_guard.py digest pending.json --verify
python3 scripts/checkpoint_guard.py --self-test
~~~

All input files are local JSON exports of the logical records defined in
[contracts.md](contracts.md). A transition's packets file is an array of EvidencePacket
objects. Omit --packets for a transition with no source coverage advance.
The cutoff is the run's frozen retrieval cutoff, not its finish time.
Commands print a small JSON result and exit zero on success or nonzero on rejection.
Do not put secrets in these temporary exports.

## What validation checks

- Supported schema, positive integer OnMove IDs, nonempty stable tracker/squad IDs,
  required checkpoint IDs/timestamps, and pending null.
- Valid lifecycle state and unique register IDs across open_loops, decisions,
  questions and conflicts.
- Terminal records with a nonempty reason, evidence references and resolution time.
- Source partition identities, basis and timestamps; complete_through cannot exceed
  the checkpoint's as_of.
- Strict JSON parsing rejects duplicate keys and non-finite values.

This is a small set of critical invariants, not a complete JSON Schema or an
exhaustive semantic review of every optional field.

## What transition checking adds

Require the same tracker, scope identity and record type, a new checkpoint ID and
a predecessor link to the previous committed checkpoint. as_of cannot regress or
exceed the supplied cutoff.

Preserve every active open loop, unanswered question, unresolved conflict and
operative decision. An active ID may remain in its registry, become an evidenced
terminal record, or become a terminal breadcrumb with registry, id, state and
resolution. A durable carry record retains an inline registry stub with the same
ID/state and its carry_ref. The guard cannot verify that external carry content is
accessible or complete; the coordinator must do so before relying on it.

Retain old source partitions. Changing provider, scope, scope_fingerprint or basis
under the same partition key is rejected: create a new key and baseline while
retaining the old state for provenance. Coverage cannot regress or disappear.

Each complete_through advance needs a matching current-run EvidencePacket with the
same partition key, fingerprint and basis, complete true and a through no later
than the frozen cutoff. The candidate's own last_attempt must also be complete and
cover the new boundary. For change_stream and best_effort_search, complete intervals
must cover the advance without gaps. A new partition establishes only its explicitly
declared initial window. For current_snapshot and finite_watchlist, a complete
packet must have the exact new boundary; that establishes a checked snapshot,
not continuous historical event coverage.

The guard does not mistake a partial packet, latest event timestamp or another
partition's successful collection for a complete coverage receipt.

## Digest receipt convention

Prepare the full planned_update, including the real request object. The final
narrative paragraph and final top-level richText paragraph must initially contain
exactly PAYLOADDIGEST PENDING. Its rich-text node has exactly type paragraph and
one child of type text with that text. The narrative separates this final paragraph
with two newlines and has no trailing newline.

The digest command removes only those two designated representations before hashing
the immutable projection specified by the contracts. The COMMIT marker, target,
attribution, semanticPath, date/state, other request content and saved candidate
remain in the hash. Replace PENDING with the output in both places and put the
same value in PendingWrite.payload_digest. Then run digest --verify before reserving.

During recovery, digest --verify rejects altered proposed content, mismatched saved
or embedded values, duplicate/decorated receipt nodes and unsupported hash values.
Mutable pending phase and server receipt fields are excluded from the hash; they
still require manual verification. Appending a returned UpdateRef to a promoted
copy does not change the immutable saved proposal. A changed saved proposal must
be reconciled, not silently rehashed.

The encoding uses sorted compact UTF-8 JSON and SHA-256. Hash inputs permit only
integer JSON numbers; use decimal strings for fractional measures. No Unicode
normalization or hidden whitespace normalization occurs.

## Regression coverage

The built-in self-test exercises quiet checkpoints, valid coverage advances,
partial/missing/wrong-scope/future/gapped receipts, each active registry's preservation,
supported and unsupported closures, tombstones, source changes, new baselines,
snapshot coverage, pending-state rejection, integer identity checks, duplicate
JSON keys, canonical digest ordering, receipt exclusion and tamper detection.
It uses synthetic local objects and performs no service writes.
