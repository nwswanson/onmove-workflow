---
name: my-synthesize-focus
description: Synthesize validated squad assessments into a focus-level management brief. Use as the squad tracker's read-only rollup subskill to identify cross-squad dependencies, decisions, shared patterns, coverage gaps, and proposed focus-note changes.
---

# Synthesize the squad-tracking focus

Read [the shared contracts](../../references/contracts.md). Use the focus settings, squad registry, prior focus context, accepted squad results, checkpoint references, and source coverage supplied by the coordinator.

Return a management brief and proposed focus-note changes. The coordinator is the sole writer. Do not call a hypothetical focus-update API: onmove has no direct focus-post operation in the verified integration. Let the coordinator persist the result using the adapter's supported objects and operations.

## Establish the scope

1. Match results to stable squad IDs and the current registry. Account for squads that were skipped, blocked, partially observed, renamed, transferred, or archived.
2. Preserve each result's cutoff and freshness. Distinguish a current assessment from carried-forward context. Do not describe stale or partially observed results as fully checked today.
3. Check that important conclusions have source references and that cross-squad statements remain consistent with the underlying assessments.
4. Keep source coverage separate from delivery outlook. Consolidate a shared connector outage once and identify affected squads.

## Find what matters across squads

Prioritize changed outcomes, risks to explicit commitments, decisions requiring the manager, dependencies crossing squad boundaries, and management follow-ups that are due or newly actionable.

Connect the same dependency, project, decision, or source event across squad results. Use stable evidence and work-item identifiers to avoid counting the same event repeatedly. Preserve the relevant perspectives and owners; do not collapse distinct obligations because they concern the same project.

Do not infer ownership from who mentioned a problem or who appears most active. Flag unconfirmed ownership and ask the smallest useful question. Do not assign work or modify another team's commitments.

Separate:

- A local incident with limited applicability.
- Repeated evidence within one squad.
- A possible shared pattern supported by independent observations across squads.
- An established global policy or accepted organizational change.

Do not promote a repeated habit or shared failure into policy. Propose an explicit policy review when warranted, with evidence, expected benefit, and the authority needed. Keep required, default, and squad-owned boundaries intact.

## Reconcile conflicts and questions

Check whether apparent contradictions reflect different dates, scope, definitions, authority, or freshness. Preserve unresolved material conflicts and their consequences. Do not use majority voting or a blanket preference for one connector.

Merge duplicate questions by the decision they would resolve. Preserve the links back to affected squads and their question IDs so an answer can resolve the right records. Prioritize decisions that unblock work or change the manager's next action. Carry lower-priority questions forward without repeatedly presenting all of them.

Recognize manager capacity: identify a small actionable set of interventions and distinguish immediate decisions from the watch list. Do not create deadlines, promise meetings, contact people, or mark actions complete.

## Write the brief

Lead with the most consequential change since the prior accepted run. If nothing material changed, say so and identify the checked scope and limitations without manufacturing news.

Use this structure, omitting empty sections:

1. **Current picture:** a concise narrative of the portfolio's outcomes and material uncertainty.
2. **Changes by squad:** short evidence-linked changes, not copies of every squad report.
3. **Manager attention:** action, reason, confirmed owner or owner gap, and explicit timing if established.
4. **Cross-squad dependencies and decisions:** connected work and unresolved decisions.
5. **Questions:** the few answers that would materially change the next step.
6. **Coverage:** skipped or partial sources, stale context, and remaining retrieval limitations.

Prefer text to a composite color. If colors are requested, retain the configured meanings and explain each underlying condition. Do not average colors or invent a numerical health score.

Compare delivery measures only when work-item definitions, workflow boundaries, observation periods, and coverage support the comparison. Do not rank squads or people by points, commits, messages, or raw throughput. Explain system constraints and differing work when a comparison is useful.

## Return to the coordinator

Use the shared synthesis contract. Include the brief, supporting squad/checkpoint references, cross-squad dependency changes, deduplicated questions with their original IDs, and proposed focus-note edits.

Propose focus-note changes only for shared settings, squad registry changes, current portfolio context, shared unresolved decisions, or confirmed cross-squad agreements. Keep squad-specific project details and coaching in the squad's thread. Identify the authority and evidence for configuration changes; distinguish proposals from accepted decisions.

Check that every squad is accounted for, no stale result gained false freshness, no source event was double-counted, no open action was lost, and no local adaptation silently changed a global rule.
