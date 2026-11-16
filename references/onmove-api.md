# Verified OnMove adapter

Read this before binding the checkpoint subskill to OnMove. Discover live tool schemas
on each new harness connection; these verified shapes are an adapter reference, not
permission to call absent tools or send conceptual state fields as API arguments.

## Contents

1. Capability and identity
2. Bootstrap and canonical Note discovery
3. Bounded reads
4. Revision-guarded notes
5. Appending updates
6. Search markers and optional tags
7. Retry, recovery, and compaction constraints
8. Verified sources

## Capability and identity

Verified against `nwswanson/onmove` commit
`380f318252a5d8a73737a578777ef0de3a4f1f6b` on 2026-11-16.

- OnMove runs a local Streamable HTTP MCP server in the open desktop application.
  Default endpoint: `http://127.0.0.1:47832/mcp`; the port is configurable.
  A cloud harness's localhost is not the user's Mac. Use an already authorized
  reachable connector/bridge when remote; never claim connectivity from this URL alone.
- Enable the server and grant the needed View/Edit capabilities in OnMove settings.
  View ordinarily defaults on; Edit/Delete and sensitive access default off.
  Never change these permissions through the skill or infer hidden records from errors.
- Focuses contain Threads; each default Note is created with its owner. No MCP
  `create_note` tool is advertised in this version. Resolve the existing `Default` Note.
- Updates can belong only to a Thread or Commitment. A Focus cannot own an Update.
  Keep the current portfolio summary/run ledger in the Focus Note. This tracker
  requires a dedicated **Team oversight** Thread under that same Focus for
  chronological portfolio risks, callouts, decisions, and steering. Record its
  returned Thread and Note IDs in the Focus registry; exclude it from the squad list.
  This is the adapter for requested focus-level posts, not a separate Focus.
- IDs are positive integers, distinct per entity kind. Preserve returned `{type,id}`,
  canonical codes, hierarchy, and ready `markdownLink` values. Do not interchange a
  matched Update ID with its containing Thread ID.
- Focus/Thread lifecycle `status` is `active|paused|done|cancelled`; Update evidence
  `state` is `red|yellow|green|none`. These fields are unrelated to tracker run status.
- Duplicate titles are permitted. Exact path lookup is case-insensitive and returns
  ambiguity instead of selecting a candidate. Never create a duplicate after an
  inaccessible/missing result without resolving the uncertainty.

## Bootstrap and canonical Note discovery

Bootstrap is explicit setup work. A normal refresh must not create a replacement
Focus, Thread, or Note just because a configured ID is unavailable.

1. Prefer previously configured IDs. Otherwise discover visible candidates with the
   tracker marker/name and compact inventory, including every lifecycle status.
   Inspect candidate hierarchy and canonical Note content before claiming a match.
   FTS similarity and a title alone do not establish tracker identity.
2. Reuse an existing tracker only when its stable identity and hierarchy match.
   For title-based resolution, require `status:"resolved"`, exactly one candidate,
   and a target whose returned IDs match the intended hierarchy. An ambiguous result
   requires an exact binding or one targeted question; never select the first hit.
3. Create a new owner only when setup intends a new tracker/squad, successful
   complete discovery finds no intended visible owner, and there is no unresolved
   configured-ID, permission, pagination, or prior-create uncertainty. A timeout,
   denied read, incomplete search, or hidden/missing ID does not prove absence.
   If an existing tracker was expected, ask about the binding/access instead.

To create the new top-level owner, call `onmove.create_focus`, for example:

```json
{"title":"Squad tracking","status":"active"}
```

The exact supported fields are `title`, optional description `richText`, `status`,
`dueDate`, `needsReview`, and `sensitive`. Do not send a note, checkpoint, registry,
scope, or caller-selected ID as an extra argument. Creation returns the Focus context
with its new ID and auto-created Default Note. Record both IDs immediately and
initialize the Note through the revision-guarded workflow below. If creating the
Focus times out, inspect discovery results and the exact intended setup identity
before retrying; creation has no deduplication key.

Under the returned Focus, create the mandatory oversight Thread and each confirmed
squad binding separately with `onmove.create_thread`, for example:

```json
{"focusId":12,"title":"Team oversight","status":"active","reviewFrequencyDays":7}
```

The exact supported fields are `focusId`, `title`, `status`, `dueDate`,
`reviewFrequencyDays`, `needsReview`, and `sensitive`. Review cadence is a positive
whole number and defaults to 7 days; `needsReview` defaults true. Use the configured
cadence rather than treating the example as a policy. New Threads inherit the
Focus's scope; creation does not expose a scope argument. Inspect the returned
write guide rather than assuming unscoped attribution for an existing bounded Focus.
Persist a created Thread's ID before attempting another create.

For an explicitly requested rename or lifecycle/cadence adjustment, the verified
onmove.update_thread accepts id plus optional title, status, dueDate,
reviewFrequencyDays, needsReview, and sensitive. It does not change parent or
Scope and has no revision guard. Re-read selected current fields, change only
requested fields, verify the result, and record partial success if the Note/registry
update fails. Internal tracker lifecycle retired maps to done or cancelled only
when an authorized disposition establishes which one. Never equate retirement with
resolution of outstanding obligations. Do not reparent Threads for ordinary project
handoffs; keep all squad Threads under their configured Focus.

For each owner, select the single returned directly owned Note titled `Default`
and record its own ID. If its content already exists, preserve it and append/update
only the tracker's managed sections. If the owner is known but its Note ID is not,
resolve the exact direct path:

```json
{"focusTitle":"Squad tracking","noteTitle":"Default"}
```

For the oversight or a squad Note, also supply the exact `threadTitle`. The tool is
`onmove.get_note_by_path`; accept only a resolved single target with the intended
owner. If titles are duplicated, use the already known owner ID to narrow note
search, hydrate candidate Note IDs, and check their parent/hierarchy. If multiple
direct Notes remain plausible or none is accessible, request the canonical binding
or the missing Note/access repair. Do not invent `create_note`, adopt a descendant
Note, replace the owner, or silently repurpose an unrelated document.

After all required IDs and Notes are verified, persist the Focus registry and
configuration. Setup is partial until the mandatory Team oversight binding exists.
Report partial setup truthfully and resume from verified IDs; do not erase the
successful pieces or create duplicates to restart.

## Bounded reads

Use stored Note IDs for normal runs:

```json
{"id":81}
```

Call `onmove.get_note_by_id` with those arguments. Returned `note.content` is readable
Markdown; `note.revision` is the current edit revision. The Note response includes its
own parent and full hierarchy, so validate it against the registry.

All numeric IDs in these examples are illustrative. Replace them with actual IDs.

For discovery, use `onmove.list_focuses({limit,offset,statuses?})` and
`onmove.list_threads({focusId,limit,offset,statuses?})`. Limits are 1–100 and offsets
0–10000. Scoped Threads may produce several Subject projection rows; deduplicate by
the durable Thread reference, not display text. Inventory contains no child Updates
or Notes. `onmove.get_note_by_path` accepts exact title fields:

```json
{"focusTitle":"Squad tracking","threadTitle":"Example squad","noteTitle":"Default"}
```

Alternatively use scoped `onmove.search` with `kinds:["note"]`, inspect hierarchy, and
hydrate the selected ID. Do not rely on a search snippet as the complete Note.

**Avoid `get_thread_by_id` for routine checkpoint loading:** it returns every visible
direct Update without a limit. The internal direct collection is ordered by recorded
date, then ID, ascending. `includeRichText:false` removes ASTs, not history volume.

Resolve the current write target without returning history:

```json
{"focus":{"id":12},"thread":{"id":19}}
```

Call `onmove.resolve_work_target`. Inspect `status`, `target.hierarchy`,
`target.writeGuide.createUpdate`, and `target.recommendedUpdateRequest`. The server
internally reads the parent, but this response returns compact target data. Copy
the recommended request's parent/attribution/semanticPath; add only the intended
date, richText, state, and sensitivity. A scoped parent may require a Subject choice.

There is no `list_updates`. For a bounded interval, call `onmove.search`:

```json
{
  "text":null,
  "kinds":["update"],
  "scope":{"mode":"thread","threadId":19},
  "lifecycle":{"mode":"all"},
  "updatedAt":{"from":"2026-11-13","to":"2026-11-16"},
  "timeZone":"America/Chicago",
  "sort":{"field":"updatedAt","direction":"asc"},
  "page":{"size":25,"maxBytes":32768}
}
```

- `date` filters the Update's effective recorded calendar date, unchanged by timezone.
  `createdAt`/`updatedAt` filter server instants through **inclusive local-date ranges**.
  They are not precise timestamp cursors. Re-read boundary dates and deduplicate.
- Use `updatedAt` to find edits and newly created backdated evidence. `createdAt`
  finds new records but misses later edits. Neither property is user-settable at create.
- A Thread scope may also match descendants: inspect each result's actual parent.
- Set explicit `lifecycle` so changing the app's closed-work preference cannot change
  recovery scope. Use `all` for intentional recovery of known tracker history.
- Search pages are at most 25 records; `page.maxBytes` ranges 8192–131072, default 32768.
  Snippets are bounded excerpts. Follow `hasMore` with `onmove.continue_search` using
  only the returned `continuationToken`; never manufacture or persist it as a watermark.
- Handles expire after three hours or server restart. Writes can stale the search
  generation. Complete relevant reads before writes; on stale/expired handles restart
  the exact query and deduplicate. Treat budget exhaustion as incomplete coverage.
- Hydrate selected records with `get_update_by_id({id})` or
  `get_updates_by_ids({ids:[...],maxBytes:32768})` (1–50 IDs). Handle `omittedIds` and
  `unavailableIds` explicitly; a partial bulk response is not complete evidence.
- For a pending append marker, use `search_updates` with nonempty literal `text`,
  exact Thread scope and `lifecycle:{mode:"all"}`. Search the alphanumeric marker,
  then hydrate and compare the full marker, actual parent, and semantic payload.
  FTS matching is candidate retrieval, not uniqueness enforcement. Do not restrict
  this search to effective `date`, because the post may be backdated.

## Revision-guarded notes

Before a structural edit, call `get_note_by_id({id,includeRichText:true})`. Copy its
`note.richText`, retain all human-owned nodes, change only tracker-owned blocks, and
call `onmove.update_note` with exactly:

```json
{
  "id":81,
  "expectedRevision":4,
  "richText":{"version":1,"blocks":[
    {"type":"paragraph","children":[{"type":"text","text":"Example preserved note text"}]},
    {"type":"paragraph","children":[{"type":"text","text":"Tracker checkpoint: example"}]}
  ]}
}
```

This is an illustrative document, **not** a template for overwriting an existing Note.
`richText` is the only writable full-document field; `content`, raw Markdown, and
`document` are not accepted. Do not send pseudo-fields such as `watermark` or `run_id`
as API arguments; serialize tracker state inside visible rich-text content.

For one exact inline change, `onmove.patch_note_text` accepts `id`,
`expectedRevision`, `findText`, optional `replaceText`, `occurrence`, `addMarks`, and
`removeMarks`. A match cannot span paragraphs/list items or line breaks. Multiple
matches require a one-based `occurrence`; do not guess it. For multi-block state use
the full AST route. Visible boundary labels and compact JSON paragraphs survive the
API; HTML comments, Markdown fences, heading/code/table nodes are not part of its AST.

The rich-text AST supports paragraphs, bullet/numbered/check lists, nested lists,
quotes, text, links, and soft line breaks. Marks are bold, italic, underline,
strikethrough, and highlight. Links accept only http/https/mailto. An `onmove://` URI
can be recorded as plain text; do not place it into a forbidden richText link node.
Preserve actual external evidence links as link nodes. No arbitrary node metadata.

On `note_revision_conflict`, re-read, reconcile human edits, and retry the intended
change with the new revision. Never drop the guard. Successful writes return a
refreshed Note with its new revision. `NOTE_TEXT_DISAPPEARED` protects accidental
clearing; checkpoint/compaction never needs `clear:true`. If lossless content is
unavailable due to a newer unsupported format, stop the structural write.

## Appending updates

The current `onmove.create_update` schema accepts only `parent`, `attribution`,
`semanticPath`, legacy `subjectId`, `date`, `richText`, `state`, and `sensitive`.
Prefer named `attribution` from the resolved write guide. Example for an Open parent:

```json
{
  "parent":{"type":"thread","id":19},
  "attribution":{"mode":"unscoped"},
  "date":"2026-11-13",
  "richText":{"version":1,"blocks":[
    {"type":"paragraph","children":[{"type":"text","text":"Delivery remains uncertain: acceptance criteria are unresolved."}]},
    {"type":"paragraph","children":[{"type":"text","text":"TSRUN0123456789abcdef; observed_at=2026-11-16T17:00:00Z; effective_date=2026-11-13"}]}
  ]},
  "state":"none"
}
```

Copy `semanticPath` when supplied by the resolver; it is mandatory for a named Subject
destination. Scoped parents require an applicable Subject; do not invent an aggregate
Subject or flatten attribution. Past dates may fail when Subject applicability differs.

`date` is a `YYYY-MM-DD` local date, defaults to today, and permits backdating.
Store exact source/event/observation instants inside the text when needed. The server
returns independent `createdAt`, `updatedAt`, `observationRevision`, and an observation
write guide. There is no client-selected ID, idempotency key, arbitrary metadata field,
or multi-tool transaction. Create the complete nonblank narrative in one call.

Omitted `state` becomes `none`. This is an actual state, not "keep the previous color".
The latest effective-date/ID Update contributes to Thread health and review freshness.
Use note-only technical/no-change checkpoints. Prefer textual substantive updates;
only assign color when configured and supported by the assessment. Do not infer that
an automated post completed a manager's coaching or check-in obligation.

To correct existing Update metadata, `onmove.update_update` accepts `id` plus
optional `date`, `state`, and `sensitive`; it does not accept observation text or a
revision guard. Localized observation edits use `patch_rich_text`, and structural
replacement uses `update_rich_text`, with
`target:{type:"update-observation",updateId}`, the fresh `expectedRevision`, and the
appropriate text patch or full `richText`. Prefer a visible corrective post when
changing a substantive conclusion; do not rewrite historical evidence silently.

## Search markers and optional tags

Plain alphanumeric markers such as `RISKCALLOUT`, `DECISIONNEEDED`, and a unique run
marker are searchable in current Notes and Update observations. Scope searches to
the intended Focus/Thread, hydrate candidates, and compare exact identifiers and
current lifecycle state. Historical occurrences of an open-risk marker do not mean
that the risk remains open; the current register and explicit resolution prevail.

OnMove also derives a tag index from inline tokens such as `@squadrisk` and
`@squaddecision`. Tags are optional navigation aids, not separate state records or
uniqueness constraints. Use ASCII letters/numbers for tracker tags: the general
plain-text tag parser accepts Unicode letters/numbers, but this revision's explicit
rich-text `tag:true` validator is narrower (`^@[A-Za-z0-9]+$`). Hyphens and underscores
are invalid tag continuations. Identity is canonical lowercase.

An explicit rich-text tag run can be:

```json
{"type":"text","text":"@squadrisk","tag":true}
```

Call `onmove.list_tags({})` for discovery and
`onmove.get_tag_uses({name:"squadrisk",limit:25,offset:0})` for uses. The name omits
`@`; limit/offset follow the bounded list schema. These tools are workspace-wide,
so validate each returned hierarchy before using a result. Lexical markers and
tags support exact follow-up discovery; semantic `retrieve` can recall related
evidence inside an already established identity boundary but cannot choose a write
target or prove that a post is absent.

## Retry, recovery, and compaction constraints

1. Reserve the pending run in the Note using its exact revision before appending.
2. Give every planned post a stable alphanumeric marker and semantic payload digest
   inside its visible body. Use the exact final PAYLOADDIGEST paragraph and canonical
   projection defined in contracts.md to avoid hashing the digest into itself.
   Retain marker, target, date, and proposed transition in
   the pending Note. The service does not enforce marker uniqueness.
3. After an ambiguous create result, find/hydrate that marker before any retry. One
   matching payload recovers its ID; conflicting or duplicate matches require
   reconciliation. Incomplete search cannot prove absence. Do not blindly append.
4. Finalize the Note by CAS after confirming the post ID/body. If finalization fails,
   leave pending state for recovery; do not advance a separate global success cursor.
5. Note CAS protects the checkpoint write, not a subsequent Update append. A pending
   marker is a cooperative reservation, not a server lease/fencing token. Serialize
   complete runs; do not take over merely because a timer expired while another run
   may still be alive. Preserve user edits when recovering.
6. Each command is internally transactional; the reserve/append/finalize sequence is
   not. No exposed note-history read/restore tool exists in this version. Keep the
   current checkpoint sufficient without history and retain explicit breadcrumb IDs.
7. Compact by rewriting only tracker-owned summary blocks and retaining open loops,
   unresolved contradictions, source coverage, and source pointers. Never delete old
   Updates for compaction: deletion is destructive, separately permissioned, and the
   archive is bounded to 30 days, not a durable audit store.

## Verified sources

- [MCP contract and operational setup](https://github.com/nwswanson/onmove/blob/380f318252a5d8a73737a578777ef0de3a4f1f6b/docs/mcp-server.md)
- [Exact tool schemas, resolver response, and search budgets](https://github.com/nwswanson/onmove/blob/380f318252a5d8a73737a578777ef0de3a4f1f6b/src/mcp/server.ts)
- [Application read projections and transactional commands](https://github.com/nwswanson/onmove/blob/380f318252a5d8a73737a578777ef0de3a4f1f6b/src/main/application/services.ts)
- [Update timestamps, ordering, and derived state](https://github.com/nwswanson/onmove/blob/380f318252a5d8a73737a578777ef0de3a4f1f6b/src/main/data/work-model.ts)
- [Rich-text schema](https://github.com/nwswanson/onmove/blob/380f318252a5d8a73737a578777ef0de3a4f1f6b/src/shared/rich-text-document.ts)
- [Plain-text tag recognition](https://github.com/nwswanson/onmove/blob/380f318252a5d8a73737a578777ef0de3a4f1f6b/src/shared/text-tags.ts)
