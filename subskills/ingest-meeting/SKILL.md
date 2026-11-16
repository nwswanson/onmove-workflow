---
name: my-ingest-meeting
description: Extract squad and project evidence from user-supplied Zoom or other meeting transcripts and notes. Use when a transcript is attached or explicitly reachable. Provide the portable intake contract for a future HOSTSYSTEM file/Zoom adapter; do not claim automatic HDD or Zoom ingestion.
---

# Ingest meeting evidence

Read [contracts](../../references/contracts.md) and use
[meeting-manifest](../../assets/templates/meeting-manifest.yaml). This subskill is
usable for supplied text/files now; automatic discovery and transport are an explicit
future adapter seam. Return read-only EvidencePackets. The coordinator persists them.

## Establish the input

Accept pasted text, VTT, SRT, plain text, or a readable supplied document through the
host's authorized file interface. A named file on someone else's HDD is not accessible
without a supplied file, selected directory or configured connector. Ask for the file
or manifest binding if needed and continue other tracking work.

Require or mark unknown: meeting_uid, source content/version digest, meeting title, meeting
date/time/timezone, transcript coverage, intended squad/project, source locator and
available speaker mapping. Derive only what file metadata reliably establishes.
Do not infer a meeting date from upload time or a speaker identity from a first name.

Keep meeting/event time, transcript creation/modification time and observed_at
distinct. A transcript imported weeks late is new evidence of an earlier event.
Give revised transcripts a new version/digest and link corrections to prior extraction.

## Extract evidence, not a personnel record

1. Read enough surrounding turns to distinguish question, proposal, disagreement,
   decision, promise, estimate and accepted action.
2. Extract project intent/scope/acceptance changes, decisions and their decision
   authority, blockers/dependencies, verification/rollout claims, explicit ownership,
   squad practice observations, retro items and manager check-ins.
3. Preserve evidence anchors: file/source ID, version digest and timecode or stable
   line/paragraph range. Include a short necessary excerpt or faithful paraphrase.
   If the source is not durably reachable, retain sufficient cited text/context for
   later verification and label the limitation; a local path alone is not durable.
4. Distinguish named speaker label from verified person identity and reported events
   from independently verified outcomes. Preserve uncertain transcription, negation,
   interruptions, missing segments and conflicting decisions.
5. Link Jira issues, project documents and GitHub proof only when evidence establishes
   the mapping. Propose unresolved associations as questions.
6. Separate squad-level process/coaching observations from individual performance
   commentary. Do not extract unrelated personal disclosures into the tracker.
7. Do not count a transcript's repetition of a Slack claim as independent confirmation
   unless it supplies separate evidence. Do not treat an action suggestion as accepted.

Represent inferred meeting function from outputs cautiously. A session titled
refinement may include planning; ask whether its required readiness outcome occurred.
A transcript truncated before the final decision cannot establish that no decision
was made.

## Coverage and duplicate handling

Use one stable partition per configured meeting intake source/scope; identify each
meeting and version independently. A complete supplied file is complete for that
file, not all meetings for that squad or week. Missing transcript segments remain gaps.

Deduplicate the same file/version and repeated import. Correct earlier claims when
a revised transcript changes them, retaining the prior version reference. Do not
advance unrelated Jira/Slack or all-meetings coverage from one transcript.

The extractor can return evidence even if date, speaker or project is unconfirmed,
but do not backdate an Onmove Update or assign an obligation from ambiguous metadata.
Ask only the questions that affect interpretation or persistence.

## Future adapter seam

A future adapter supplies a MeetingManifest and readable content to this same skill.
It should enumerate only configured locations, retain source file identity and version,
record ingestion progress, surface inaccessible/partial files, and provide durable
evidence locators. Decide the actual Zoom/local-file transport in HOSTSYSTEM later.

Do not install watchers, read arbitrary disks, upload raw transcripts to new services,
or create a schedule as part of this stub. Leave transport.mode as supplied until an
explicit integration is configured. For this run return how the supplied content was
accessed and what future coverage remains unavailable.

## Return contract

Return EvidencePacket(s), meeting metadata/version, extracted anchored claims,
candidate project/watchlist associations, question/decision/action proposals,
coverage limitations and duplicate/correction relationships. Mark certainty and
event time independently. Do not write Onmove or contact participants.
