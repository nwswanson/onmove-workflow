# HOSTSYSTEM integration and portable loading

Read this reference when installing the bundle, configuring a native HOSTSYSTEM
agent, or adapting the coordinator to another harness. Keep squad configuration
and tracking state in onmove; this integration does not create a second state store.

Contents: [Verified basis](#verified-basis) ·
[Skill loading](#load-one-root-skill-and-explicit-subskill-files) ·
[Native agent](#optional-native-on-demand-coordinator) ·
[Delegation](#delegate-without-coupling-the-core-to-one-runtime) ·
[Connectors](#connectors-and-deployment-limits) ·
[Sources](#primary-references)

## Verified basis

Inspected on 2026-11-16:

- `HOSTSYSTEM_ORG/HOSTSYSTEM-releases` at commit
  `9ad8d118597796674e8dafbab86dbf625ad614d6` contains release artifacts and a short
  README, not the application implementation.
- The official `HOSTSYSTEM_ORG/td-skills` repository at commit
  `7c1015d996b262c9266114961497dcb02a7c993e` contains current HOSTSYSTEM authoring
  instructions. Its Work-specific skills use the `mcp__work__*` namespace.
- Deprecated Studio documentation describes compatible skill directories and MCP
  connections. Treat those UI instructions as a starting
  point; confirm the installed HOSTSYSTEM build's actual tools and settings.

Do not claim this bundle has been installed or executed in HOSTSYSTEM merely
because its files pass local validation.

## Load one root skill and explicit subskill files

The installable root is the complete `my-squad-tracker/` directory. Its `SKILL.md`
has standard `name` and `description` frontmatter. Preserve its `references/`,
`subskills/`, and `assets/` directories when distributing it.

Register or enable the root skill. The coordinator explicitly reads the subskill
files named in its instructions, relative to its own skill package. Nested
subskills do not depend on recursive skill discovery and need not become separate
entries in the harness's skill menu. Resolve their resources through the same
mechanism used to load the root: filesystem reads for a filesystem package, or
the host's resource API for a hosted package. Never treat a resource URI as a
filesystem path.

HOSTSYSTEM's official skill-creator instructions identify `write_skill` as the
custom skill creation/update tool. They do not publish its complete argument
schema or a verified custom-skills filesystem root. Discover that tool's live
schema before calling it. Do not assume writing only the root Markdown file also
installs its supporting files. If the available tool handles a single file only,
use the build's supported full-directory or package installation mechanism for this
bundle. Report missing supporting files instead of running a partial installation.
Do not invent a `~/.HOSTSYSTEM/skills` path or promise a ZIP-import facility that
has not been observed.

## Optional native on-demand coordinator

The template is `assets/HOSTSYSTEM/AGENTS.md`. It contains no schedule,
notification target, model override, guessed skill ID, or squad identifiers.
Its body resolves the installed root skill by canonical name. The root skill
handles onmove focus discovery and initial configuration.

The current official Work agent format is YAML frontmatter plus a Markdown system
prompt. Global agents live at `~/.HOSTSYSTEM/agents/{name}/AGENTS.md`; workspace
agents live at `{workspace}/agents/{name}/AGENTS.md`. Prefer `agent_create` and
`agent_update`, which validate their inputs. Inspect their current schemas and map
the template's frontmatter plus body to the supported arguments. These mutations
are global-only in the inspected instructions; workspace edits use AgentSettings.

Leave a newly installed agent in `status: draft` while testing. Use
`agent_run_now` for an authorized manual run and inspect its returned `chatId`
with `chat_read` until `in_progress` becomes false. Review the actual result before
marking it active. Omitting `schedule` keeps an active agent on-demand: it can be
invoked by its UI control, chat or mention without a cron trigger. Do not enable
recurrence or Slack notifications as part of this manual-only workflow.

The template omits `allowed_tools` because connector names vary by installation.
In the inspected Work schema, omission or an empty list allows all controllable
tools; it is not a read-only boundary. Where tool-level restriction is needed,
discover the actual connector tools and configure a concrete allowlist with the
host-supported identifiers. Work's internal tool allowlist uses short names.
Keep source connectors read-only and restrict onmove mutations to the coordinator's
authorized operations. Instruction-level worker restrictions do not replace an
available tool permission boundary.

Current tools are `agent_create`, `agent_list`, `agent_get`, `agent_update`,
`agent_delete`, `agent_run_now`, and `chat_read`. Do not substitute the retired
`TASK.md` / `schedule.yaml` format, `schedule_*` tools, `enabled`, `cron`,
`permissions.allow`, or nested `context.*` settings.

## Delegate without coupling the core to one runtime

The official Work agent-review skill uses `TaskCreate` for parallel subagents and
`TaskGet` for collection. Discover the available execution tools and their schemas
at runtime; other harnesses use different names and concurrency limits.

Use the coordinator's natural-language delegation contract: up to N workers, one
independent squad assessment per worker, followed by synthesis after assessment
results arrive. Give each worker the applicable subskill text or accessible
resource, resolved configuration, checkpoint, evidence or source scope, and
required output contract. Workers return proposals; the coordinator alone writes
onmove. A persistent native agent is optional; transient squad workers do not
need their own installed `AGENTS.md` files.

If no subagent facility exists, execute the same subskills sequentially and report
that execution mode. Natural-language instructions cannot create absent tools.
If worker tool access differs from the coordinator's, pass the collected evidence
to the worker instead of assuming it can use the parent's MCP connections.

## Connectors and deployment limits

Discover Jira, Confluence, Slack, GitHub and onmove tools by capability and inspect
their schemas. Names in older examples are not a contract. The legacy Studio
connection guide supports Atlassian and custom HTTP/SSE MCP servers through
Settings > Connections, including OAuth; verify the current Work build's flow.
Keep credentials in the host's connection settings, never in the skill or onmove
notes. Record unavailable source coverage and continue independent work according
to the main skill. Do not claim a successful end-to-end run without live connector
results and verified persistence.

## Primary references

- [Current Work skill authoring](https://github.com/HOSTSYSTEM_ORG/td-skills/blob/7c1015d996b262c9266114961497dcb02a7c993e/HOSTSYSTEM-skills/skill-creator/SKILL.md)
- [Current Work agent schema and lifecycle](https://github.com/HOSTSYSTEM_ORG/td-skills/blob/7c1015d996b262c9266114961497dcb02a7c993e/HOSTSYSTEM-skills/work-agent/SKILL.md)
- [Current Work subagent review workflow](https://github.com/HOSTSYSTEM_ORG/td-skills/blob/7c1015d996b262c9266114961497dcb02a7c993e/HOSTSYSTEM-skills/agent-review/SKILL.md)
- [Legacy Studio skills guide](https://HOSTSYSTEM_DOCS_HOST/studio/skills)
- [Legacy Studio connection guide](https://HOSTSYSTEM_DOCS_HOST/studio/connections)
- [HOSTSYSTEM release repository](https://github.com/HOSTSYSTEM_ORG/HOSTSYSTEM-releases)
