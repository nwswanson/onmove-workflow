#!/usr/bin/env python3
"""Offline candidate/transition checks. No connector access or live persistence."""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ACTIVE = {"proposed", "agreed", "in_progress", "waiting"}
TERMINAL = {"completed", "cancelled", "superseded"}
REGISTRIES = ("open_loops", "decisions", "questions", "conflicts")
BASES = {"change_stream", "current_snapshot", "finite_watchlist", "best_effort_search"}
STATUSES = {"not_run", "complete", "partial", "failed", "unavailable"}


class GuardError(ValueError):
    """A checkable candidate invariant was violated."""


def require(condition, message):
    if not condition:
        raise GuardError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def instant(value, label):
    require(isinstance(value, str), f"{label} must be a timestamp string")
    require(bool(re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})",
        value)), f"{label} must be an RFC 3339 instant with a timezone")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc)
    except ValueError as exc:
        raise GuardError(f"{label} is not a valid instant") from exc


def nullable_instant(value, label):
    return None if value is None else instant(value, label)


def positive_id(value, label):
    require(type(value) is int and value > 0,
            f"{label} must be a positive integer OnMove ID")


def resolution(record, label):
    resolved = record.get("resolution")
    require(isinstance(resolved, dict), f"{label} needs resolution")
    require(text(resolved.get("reason")), f"{label} needs a resolution reason")
    refs = resolved.get("evidence_refs")
    require(isinstance(refs, list) and refs and all(text(x) for x in refs),
            f"{label} needs nonempty resolution evidence_refs")
    instant(resolved.get("at"), f"{label}.resolution.at")


def registry_record(record, registry):
    require(isinstance(record, dict), f"{registry} entries must be objects")
    require(text(record.get("id")), f"{registry} entry needs a stable id")
    label = f"{registry}/{record['id']}"
    require(record.get("state") in ACTIVE | TERMINAL, f"{label} has invalid state")
    if record["state"] in TERMINAL:
        resolution(record, label)


def validate_snapshot(snapshot):
    """Check a fully bound committed/candidate envelope with pending null."""
    require(isinstance(snapshot, dict), "snapshot must be an object")
    require(type(snapshot.get("schema_version")) is int
            and snapshot["schema_version"] == 1, "unsupported schema_version")
    require(text(snapshot.get("tracker_namespace")), "tracker_namespace is required")
    kind = snapshot.get("record_type")
    require(kind in {"focus", "squad"}, "record_type must be focus or squad")
    identity = snapshot.get("identity")
    require(isinstance(identity, dict), "identity must be an object")
    for name in ("focus_id", "note_id"):
        positive_id(identity.get(name), f"identity.{name}")
    if kind == "squad":
        positive_id(identity.get("thread_id"), "identity.thread_id")
        require(text(identity.get("squad_uid")), "identity.squad_uid is required")
    require(isinstance(snapshot.get("configuration"), dict),
            "configuration must be an object")
    require("pending" in snapshot and snapshot["pending"] is None,
            "candidate checking requires pending:null; recover pending writes manually")
    checkpoint = snapshot.get("checkpoint")
    require(isinstance(checkpoint, dict), "checkpoint must be an object")
    require(text(checkpoint.get("checkpoint_id")), "checkpoint_id is required")
    require(text(checkpoint.get("run_id")), "checkpoint.run_id is required")
    as_of = instant(checkpoint.get("as_of"), "checkpoint.as_of")
    instant(checkpoint.get("recorded_at"), "checkpoint.recorded_at")
    predecessor = checkpoint.get("predecessor_checkpoint_id")
    require(predecessor is None or text(predecessor),
            "predecessor_checkpoint_id must be null or a string")
    all_ids = set()
    for registry in REGISTRIES:
        entries = checkpoint.get(registry)
        require(isinstance(entries, list), f"{registry} must be an array")
        for record in entries:
            registry_record(record, registry)
            require(record["id"] not in all_ids,
                    f"duplicate active-register id {record['id']}")
            all_ids.add(record["id"])
    sources = checkpoint.get("source_states")
    require(isinstance(sources, dict), "source_states must be an object")
    for key, source in sources.items():
        require(text(key) and isinstance(source, dict), "invalid source partition")
        require(source.get("partition_key") == key,
                f"source_states/{key} must retain its partition_key")
        require(text(source.get("provider")), f"{key} needs provider")
        require(isinstance(source.get("scope"), dict), f"{key} needs scope object")
        require(text(source.get("scope_fingerprint")), f"{key} needs scope_fingerprint")
        require(source.get("basis") in BASES, f"{key} has invalid basis")
        covered = nullable_instant(source.get("complete_through"), f"{key}.complete_through")
        require(covered is None or covered <= as_of,
                f"{key}.complete_through exceeds checkpoint.as_of")
        nullable_instant(source.get("checked_at"), f"{key}.checked_at")
        nullable_instant(source.get("last_reconciled_at"), f"{key}.last_reconciled_at")
        attempt = source.get("last_attempt")
        require(isinstance(attempt, dict), f"{key} needs last_attempt")
        require(attempt.get("status") in STATUSES, f"{key} has invalid attempt status")
        require(type(attempt.get("complete")) is bool, f"{key} needs attempt complete boolean")
        nullable_instant(attempt.get("from"), f"{key}.last_attempt.from")
        nullable_instant(attempt.get("through"), f"{key}.last_attempt.through")
    breadcrumbs = checkpoint.get("breadcrumbs", [])
    require(isinstance(breadcrumbs, list), "breadcrumbs must be an array")
    for record in breadcrumbs:
        require(isinstance(record, dict), "breadcrumb must be an object")
        if record.get("registry") in REGISTRIES and "id" in record:
            registry_record(record, record["registry"])
            require(record["state"] in TERMINAL,
                    "active carry records must retain an inline registry stub")


def preserved_records(before, after):
    prior = before["checkpoint"]
    next_state = after["checkpoint"]
    for registry in REGISTRIES:
        current = {r["id"]: r for r in next_state[registry]}
        tombstones = {
            r["id"]: r for r in next_state.get("breadcrumbs", [])
            if r.get("registry") == registry and "id" in r
        }
        for record in prior[registry]:
            if record["state"] not in ACTIVE:
                continue
            target = current.get(record["id"]) or tombstones.get(record["id"])
            require(target is not None,
                    f"active {registry}/{record['id']} disappeared without a retained record")
            if target["state"] in TERMINAL:
                resolution(target, f"{registry}/{record['id']}")


def coverage_proves(key, source, previous_through, target, packets, run_id, cutoff):
    intervals = []
    snapshots = []
    for packet in packets:
        require(isinstance(packet, dict), "evidence packet must be an object")
        if (packet.get("partition_key") != key
                or packet.get("scope_fingerprint") != source["scope_fingerprint"]
                or packet.get("run_id") != run_id):
            continue
        coverage = packet.get("coverage", {})
        if (not isinstance(coverage, dict)
                or coverage.get("complete") is not True
                or coverage.get("basis") != source["basis"]):
            continue
        require(type(packet.get("schema_version")) is int and packet["schema_version"] == 1,
                f"{key} packet has unsupported schema_version")
        through = instant(coverage.get("through"), f"{key}.packet.coverage.through")
        require(through <= cutoff, f"{key} evidence coverage extends beyond cutoff")
        start = nullable_instant(coverage.get("from"), f"{key}.packet.coverage.from")
        if source["basis"] in {"current_snapshot", "finite_watchlist"}:
            if start is not None:
                require(start <= through, f"{key} has a reversed packet interval")
            snapshots.append(through)
        else:
            require(start is not None, f"{key} interval coverage needs from")
            require(start <= through, f"{key} has a reversed packet interval")
            intervals.append((start, through))
    if source["basis"] in {"current_snapshot", "finite_watchlist"}:
        require(any(t == target for t in snapshots),
                f"{key} advance lacks a matching complete snapshot/watchlist packet")
        return
    require(intervals, f"{key} advance lacks matching complete evidence")
    intervals.sort()
    # Bootstrap establishes only its declared initial window, not prior history.
    reached = previous_through if previous_through is not None else intervals[0][0]
    for start, through in intervals:
        if through <= reached:
            continue
        if start > reached:
            break
        reached = through
        if reached >= target:
            return
    require(reached >= target, f"{key} advance crosses an uncovered interval")


def validate_transition(before, after, packets, cutoff_text):
    """Check pre-reservation committed state to a proposed committed candidate."""
    validate_snapshot(before)
    validate_snapshot(after)
    require(isinstance(packets, list), "packets input must be an array")
    cutoff = instant(cutoff_text, "cutoff")
    for field in ("tracker_namespace", "record_type", "identity"):
        require(before[field] == after[field], f"{field} changed during a state transition")
    old_cp, new_cp = before["checkpoint"], after["checkpoint"]
    require(new_cp["checkpoint_id"] != old_cp["checkpoint_id"],
            "candidate needs a new checkpoint_id")
    require(new_cp.get("predecessor_checkpoint_id") == old_cp["checkpoint_id"],
            "candidate predecessor does not match the committed checkpoint")
    old_asof = instant(old_cp["as_of"], "before.as_of")
    new_asof = instant(new_cp["as_of"], "candidate.as_of")
    require(old_asof <= new_asof <= cutoff,
            "candidate as_of regressed or extends beyond cutoff")
    preserved_records(before, after)
    old_sources, new_sources = old_cp["source_states"], new_cp["source_states"]
    for key, old in old_sources.items():
        require(key in new_sources, f"{key} source state disappeared")
        new = new_sources[key]
        for field in ("provider", "scope", "scope_fingerprint", "basis"):
            require(old.get(field) == new.get(field),
                    f"{key} changed {field}; create a new partition and retain the old state")
    for key, source in new_sources.items():
        target = nullable_instant(source.get("complete_through"), f"{key}.complete_through")
        previous = old_sources.get(key, {})
        last = nullable_instant(previous.get("complete_through"), f"{key}.previous_through")
        require(last is None or (target is not None and target >= last),
                f"{key} complete_through regressed or was erased")
        require(target is None or target <= cutoff,
                f"{key} complete_through extends beyond cutoff")
        if target is None or target == last:
            continue
        attempt = source["last_attempt"]
        require(attempt.get("complete") is True and attempt.get("status") == "complete",
                f"{key} advanced with an incomplete last_attempt")
        attempted_through = instant(attempt.get("through"), f"{key}.last_attempt.through")
        require(target <= attempted_through <= cutoff,
                f"{key} advance exceeds the recorded attempt/cutoff")
        coverage_proves(key, source, last, target, packets, new_cp["run_id"], cutoff)


def integer_json(value, path="$"):
    """Canonical payload numbers are integers; avoid cross-runtime float ambiguity."""
    if value is None or isinstance(value, (str, bool)):
        return
    if type(value) is int:
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            integer_json(item, f"{path}[{index}]")
        return
    require(isinstance(value, dict), f"{path} contains a non-integer or unsupported JSON value")
    for key, item in value.items():
        require(isinstance(key, str), f"{path} has a non-string key")
        require(key != "payload_digest", f"{path} embeds payload_digest and would create a hash cycle")
        integer_json(item, f"{path}.{key}")


def digest_projection(pending):
    """Remove only the reserved final PAYLOADDIGEST paragraph from the hash input."""
    require(isinstance(pending, dict), "pending input must be an object")
    names = ("attempt_id", "base_checkpoint_id", "commit_marker",
             "proposed_snapshot", "planned_update")
    require(all(name in pending for name in names), "pending lacks immutable digest fields")
    require(text(pending["attempt_id"]), "attempt_id is required")
    require(text(pending["commit_marker"])
            and pending["commit_marker"].isascii()
            and pending["commit_marker"].isalnum(),
            "commit_marker must be ASCII alphanumeric")
    require(isinstance(pending["proposed_snapshot"], dict)
            and "pending" in pending["proposed_snapshot"]
            and pending["proposed_snapshot"]["pending"] is None,
            "saved proposed_snapshot must have pending:null")
    planned = pending["planned_update"]
    require(isinstance(planned, dict), "planned_update must be complete")
    require(set(planned) == {"thread_id", "effective_date", "state", "narrative", "request"},
            "planned_update must contain exactly thread_id/effective_date/state/narrative/request")
    positive_id(planned["thread_id"], "planned_update.thread_id")
    narrative = planned["narrative"]
    require(isinstance(narrative, str), "planned_update.narrative must be a string")
    match = re.search(r"\n\nPAYLOADDIGEST (PENDING|[0-9a-f]{64})$", narrative)
    require(match is not None and text(narrative[:match.start()]),
            "narrative must end with a separate PAYLOADDIGEST PENDING or lowercase hex paragraph")
    require(len(re.findall(r"(?m)^PAYLOADDIGEST ", narrative)) == 1,
            "narrative has duplicate reserved PAYLOADDIGEST paragraphs")
    receipt_value = match.group(1)
    request = planned["request"]
    require(isinstance(request, dict) and request,
            "planned_update.request must contain the full actual create_update request")
    require(request.get("parent") == {"type": "thread", "id": planned["thread_id"]},
            "planned_update thread_id and request.parent disagree")
    require(request.get("date") == planned["effective_date"]
            and request.get("state") == planned["state"],
            "planned_update date/state and request disagree")
    rich = request.get("richText")
    require(isinstance(rich, dict) and rich.get("version") == 1,
            "digest receipt requires the verified version-1 richText envelope")
    blocks = rich.get("blocks")
    require(isinstance(blocks, list) and len(blocks) >= 2,
            "richText needs substantive content and a final digest receipt paragraph")
    expected = {"type": "paragraph",
                "children": [{"type": "text", "text": "PAYLOADDIGEST " + receipt_value}]}
    require(blocks[-1] == expected,
            "final richText digest receipt must exactly match the narrative receipt")
    for block in blocks[:-1]:
        if not isinstance(block, dict):
            continue
        children = block.get("children", [])
        if (block.get("type") == "paragraph" and len(children) == 1
                and isinstance(children[0], dict) and children[0].get("type") == "text"):
            require(not str(children[0].get("text", "")).startswith("PAYLOADDIGEST "),
                    "richText has duplicate reserved digest receipt paragraphs")
    projection = {"schema_version": 1, **{name: deepcopy(pending[name]) for name in names}}
    projection["planned_update"]["narrative"] = narrative[:match.start()]
    projection["planned_update"]["request"]["richText"]["blocks"].pop()
    return projection, receipt_value


def payload_digest(pending):
    projection, _receipt = digest_projection(pending)
    integer_json(projection)
    encoded = json.dumps(projection, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def verify_pending_digest(pending):
    actual = payload_digest(pending)
    _projection, receipt = digest_projection(pending)
    require(pending.get("payload_digest") == actual,
            "saved payload_digest differs from the immutable semantic payload")
    require(receipt == actual, "embedded PAYLOADDIGEST receipt does not match")
    return actual


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    def bad_constant(_value):
        raise GuardError("non-finite JSON numbers are not accepted")
    return json.loads(Path(path).read_text(encoding="utf-8"),
                      object_pairs_hook=no_duplicate_keys, parse_constant=bad_constant)


def self_test():
    """Exercise preservation, source proof and hash boundaries without live data."""
    t0, t1, t2 = ("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z",
                  "2026-01-03T00:00:00Z")
    source = {
        "partition_key": "jira:a", "provider": "jira", "scope": {"board_id": "10"},
        "scope_fingerprint": "scope-a", "basis": "change_stream",
        "complete_through": t0, "checked_at": t0, "last_reconciled_at": None,
        "last_attempt": {"from": t0, "through": t0, "complete": True, "status": "complete"}
    }
    base = {
        "schema_version": 1, "tracker_namespace": "test-only", "record_type": "squad",
        "identity": {"focus_id": 1, "thread_id": 2, "note_id": 3, "squad_uid": "squad-test"},
        "configuration": {}, "pending": None,
        "checkpoint": {
            "checkpoint_id": "cp0", "predecessor_checkpoint_id": None, "run_id": "run0",
            "as_of": t0, "recorded_at": t0,
            "open_loops": [{"id": "risk-a", "kind": "risk", "state": "waiting"}],
            "decisions": [{"id": "decision-a", "state": "agreed"}],
            "questions": [{"id": "question-a", "state": "waiting"}],
            "conflicts": [{"id": "conflict-a", "state": "waiting"}],
            "source_states": {"jira:a": source}, "breadcrumbs": []
        }
    }
    candidate = deepcopy(base)
    candidate["checkpoint"].update(checkpoint_id="cp1", predecessor_checkpoint_id="cp0",
                                   run_id="run1", as_of=t1, recorded_at=t1)
    advancing = deepcopy(candidate)
    advancing["checkpoint"]["source_states"]["jira:a"].update(complete_through=t1)
    advancing["checkpoint"]["source_states"]["jira:a"]["last_attempt"].update(through=t1)
    packet = {
        "schema_version": 1, "run_id": "run1", "partition_key": "jira:a",
        "scope_fingerprint": "scope-a",
        "coverage": {"from": t0, "through": t1, "basis": "change_stream", "complete": True}
    }
    count = 0
    def check(fn, should_pass=True):
        nonlocal count
        count += 1
        try:
            fn()
        except (GuardError, UnicodeEncodeError):
            require(not should_pass, f"self-test {count} unexpectedly rejected a valid case")
        else:
            require(should_pass, f"self-test {count} accepted an invalid case")
    check(lambda: validate_snapshot(base))
    check(lambda: validate_transition(base, candidate, [], t1))
    check(lambda: validate_transition(base, advancing, [packet], t1))
    check(lambda: validate_transition(base, advancing, [], t1), False)
    partial = deepcopy(packet); partial["coverage"]["complete"] = False
    check(lambda: validate_transition(base, advancing, [partial], t1), False)
    wrong_scope = deepcopy(packet); wrong_scope["scope_fingerprint"] = "scope-b"
    check(lambda: validate_transition(base, advancing, [wrong_scope], t1), False)
    future = deepcopy(packet); future["coverage"]["through"] = t2
    check(lambda: validate_transition(base, advancing, [future], t1), False)
    gap = deepcopy(packet); gap["coverage"]["from"] = "2026-01-01T12:00:00Z"
    check(lambda: validate_transition(base, advancing, [gap], t1), False)
    for registry in REGISTRIES:
        lost = deepcopy(candidate); lost["checkpoint"][registry] = []
        check(lambda lost=lost: validate_transition(base, lost, [], t1), False)
    closed = deepcopy(candidate)
    record = closed["checkpoint"]["open_loops"][0]
    record.update(state="completed", resolution={"reason": "Verified outcome",
                   "evidence_refs": ["evidence-1"], "at": t1})
    check(lambda: validate_transition(base, closed, [], t1))
    unsupported = deepcopy(closed)
    unsupported["checkpoint"]["open_loops"][0]["resolution"]["evidence_refs"] = []
    check(lambda: validate_transition(base, unsupported, [], t1), False)
    tombstone = deepcopy(closed)
    record = tombstone["checkpoint"]["open_loops"].pop()
    record["registry"] = "open_loops"
    tombstone["checkpoint"]["breadcrumbs"].append(record)
    check(lambda: validate_transition(base, tombstone, [], t1))
    changed = deepcopy(advancing)
    changed["checkpoint"]["source_states"]["jira:a"]["scope_fingerprint"] = "scope-b"
    check(lambda: validate_transition(base, changed, [packet], t1), False)
    missing_source = deepcopy(candidate); missing_source["checkpoint"]["source_states"] = {}
    check(lambda: validate_transition(base, missing_source, [], t1), False)
    pending_base = deepcopy(base); pending_base["pending"] = {"phase": "reserved"}
    check(lambda: validate_transition(pending_base, candidate, [], t1), False)
    bad_id = deepcopy(base); bad_id["identity"]["note_id"] = True
    check(lambda: validate_snapshot(bad_id), False)
    new_scope = deepcopy(candidate)
    new_source = deepcopy(source)
    new_source.update(partition_key="jira:b", scope_fingerprint="scope-b",
                      scope={"board_id": "20"}, complete_through=t1)
    new_source["last_attempt"].update(through=t1)
    new_scope["checkpoint"]["source_states"]["jira:b"] = new_source
    new_packet = deepcopy(packet)
    new_packet.update(partition_key="jira:b", scope_fingerprint="scope-b")
    check(lambda: validate_transition(base, new_scope, [new_packet], t1))
    check(lambda: validate_transition(base, new_scope, [], t1), False)
    snapshot_base = deepcopy(base)
    snapshot_base["checkpoint"]["source_states"]["jira:a"]["basis"] = "finite_watchlist"
    snapshot_next = deepcopy(advancing)
    snapshot_next["checkpoint"]["source_states"]["jira:a"]["basis"] = "finite_watchlist"
    snapshot_packet = deepcopy(packet)
    snapshot_packet["coverage"].update(basis="finite_watchlist", **{"from": None})
    check(lambda: validate_transition(snapshot_base, snapshot_next, [snapshot_packet], t1))
    interrupted = deepcopy(advancing)
    interrupted["checkpoint"]["source_states"]["jira:a"]["last_attempt"]["complete"] = False
    check(lambda: validate_transition(base, interrupted, [packet], t1), False)
    pending = {
        "attempt_id": "attempt1", "base_checkpoint_id": "cp0", "commit_marker": "ABC123",
        "proposed_snapshot": candidate,
        "planned_update": {"thread_id": 2, "effective_date": "2026-01-02", "state": "none",
                           "narrative": "Test-only COMMIT ABC123\n\nPAYLOADDIGEST PENDING",
                           "request": {
                               "parent": {"type": "thread", "id": 2},
                               "attribution": {"mode": "unscoped"},
                               "date": "2026-01-02", "state": "none",
                               "richText": {"version": 1, "blocks": [
                                   {"type": "paragraph", "children": [
                                       {"type": "text", "text": "Test-only COMMIT ABC123"}]},
                                   {"type": "paragraph", "children": [
                                       {"type": "text", "text": "PAYLOADDIGEST PENDING"}]}
                               ]}
                           }},
        "phase": "reserved", "receipt": None
    }
    digest = payload_digest(pending)
    changed_receipt = deepcopy(pending)
    changed_receipt.update(phase="appended", receipt={"update_id": 10}, payload_digest=digest)
    check(lambda: require(payload_digest(changed_receipt) == digest, "receipt changed digest"))
    changed_body = deepcopy(pending)
    changed_body["planned_update"]["narrative"] = changed_body["planned_update"]["narrative"].replace(
        "Test-only", "Changed")
    check(lambda: require(payload_digest(changed_body) != digest, "payload did not change digest"))
    changed_order = dict(reversed(list(pending.items())))
    check(lambda: require(payload_digest(changed_order) == digest, "key order changed digest"))
    floating = deepcopy(pending); floating["proposed_snapshot"]["configuration"]["metric"] = 0.5
    check(lambda: payload_digest(floating), False)
    recursive = deepcopy(pending); recursive["proposed_snapshot"]["payload_digest"] = digest
    check(lambda: payload_digest(recursive), False)
    check(lambda: no_duplicate_keys([("a", 1), ("a", 2)]), False)
    finished = deepcopy(pending)
    finished["payload_digest"] = digest
    finished["planned_update"]["narrative"] = finished["planned_update"]["narrative"].replace(
        "PAYLOADDIGEST PENDING", "PAYLOADDIGEST " + digest)
    finished["planned_update"]["request"]["richText"]["blocks"][-1]["children"][0]["text"] = (
        "PAYLOADDIGEST " + digest)
    check(lambda: require(payload_digest(finished) == digest, "embedded receipt altered digest"))
    check(lambda: verify_pending_digest(finished))
    mismatched = deepcopy(finished); mismatched["payload_digest"] = "0" * 64
    check(lambda: verify_pending_digest(mismatched), False)
    altered_receipt = deepcopy(finished)
    altered_receipt["planned_update"]["request"]["richText"]["blocks"][-1]["children"].append(
        {"type": "text", "text": "unhashed extra claim"})
    check(lambda: payload_digest(altered_receipt), False)
    no_receipt = deepcopy(pending)
    no_receipt["planned_update"]["request"]["richText"]["blocks"].pop()
    check(lambda: payload_digest(no_receipt), False)
    changed_snapshot = deepcopy(finished)
    changed_snapshot["proposed_snapshot"]["checkpoint"]["last_substantive_update"] = {"update_id": 99}
    check(lambda: verify_pending_digest(changed_snapshot), False)
    return count


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run offline regression cases")
    sub = parser.add_subparsers(dest="command")
    validate = sub.add_parser("validate", help="validate a fully bound candidate with pending:null")
    validate.add_argument("snapshot")
    transition = sub.add_parser("transition", help="check pre-reservation committed to candidate")
    transition.add_argument("before")
    transition.add_argument("candidate")
    transition.add_argument("--packets", help="JSON array of evidence packets; default empty")
    transition.add_argument("--cutoff", required=True, help="fixed run cutoff in RFC 3339")
    digest = sub.add_parser("digest", help="hash the immutable fields of a saved PendingWrite")
    digest.add_argument("pending")
    digest.add_argument("--verify", action="store_true",
                        help="also verify saved and embedded digest receipts")
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            require(args.command is None, "use --self-test without a subcommand")
            result = {"ok": True, "self_tests": self_test(), "live_writes": False}
        elif args.command == "validate":
            validate_snapshot(read_json(args.snapshot))
            result = {"ok": True, "checked": "offline candidate structure"}
        elif args.command == "transition":
            packets = read_json(args.packets) if args.packets else []
            validate_transition(read_json(args.before), read_json(args.candidate),
                                packets, args.cutoff)
            result = {"ok": True, "checked": "offline committed-to-candidate transition"}
        elif args.command == "digest":
            pending = read_json(args.pending)
            value = verify_pending_digest(pending) if args.verify else payload_digest(pending)
            result = {"ok": True, "payload_digest": value, "verified_receipts": args.verify}
        else:
            parser.error("choose validate, transition, digest or --self-test")
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (GuardError, OSError, ValueError, UnicodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
