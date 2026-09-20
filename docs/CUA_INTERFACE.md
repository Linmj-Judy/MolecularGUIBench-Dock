# CUA interface inspection

- Skill path: `/Users/judy/project/openai4s/MolecularGUIBench-Dock/.agents/skills/byted-util-ark-cua/SKILL.md`
- Skill version: `1.0.7`
- ArkCLI: installed from `@volcengine/ark-cli@1.0.33`; `arkcli --version`
  reports `1.0.33` on Darwin arm64. Its postinstall binary download completed.
- Authentication: bundled `scripts/cua.py auth status`, with protected arkcli
  profile discovery or hidden manual login; keys must never enter this repo.
- Task lifecycle: `delegate` for the generic objective flow; `task run` for an
  explicitly selected desktop; poll the returned `next.command`/task status.
- Terminal outcomes: `completed`, `failed`, `cancelled`; `needs_input` is a
  benchmark failure (`HUMAN_ASSIST_REQUIRED`) and is never answered automatically.
- Artifacts: use registered artifacts, then `artifact list`/`artifact save`; never
  write untrusted HTML or base64 responses as files.
- Desktop/session: `desktop list`, `desktop start`, `desktop shutdown`; one task per
  desktop at a time. Contexts are not reused between episodes.
- Model/version: read-only `model get` and record metadata per run.

- Current auth probe (2026-09-20): `auth status` reports a logged-in protected
  credential cache. `desktop list` reports the caller-owned desktop
  `desk-292ef060afb933b2` as running and ready. A real Phase A task was started,
  but remains `needs_input` because the desktop workspace does not contain the
  public Astex episode; no private/native data was exposed.

The adapter intentionally reports a clear setup error when the official CLI is
unavailable rather than guessing an HTTP API.
