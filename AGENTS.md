# GARM Proxmox Provider — Implementation Plan (AGENTS.md)

Status key: ✅ done · 🚧 in progress · ⏳ pending

## Scope
- Build an external GARM provider that manages runner VMs on Proxmox VE via `proxmoxer`.
- Provide CLI entrypoint `garm-proxmox-provider` that implements all required commands: `CreateInstance`, `DeleteInstance`, `GetInstance`, `ListInstances`, `RemoveAllInstances`, `Start`, `Stop`.
- Support cloud-init bootstrap to install/configure GitHub/Gitea runners using GARM’s bootstrap payload.

## Milestones & Tasks

### Phase 0 — Scaffolding & docs
- ✅ Draft README with goals, config sketch, and roadmap.
- ✅ Write AGENTS plan with checklist (this file).
- ⏳ Add initial CLI skeleton using `click` and environment-based dispatch.

### Phase 1 — Core plumbing
- ⏳ Config loader (TOML) and validation (PVE endpoint, token, defaults).
- ⏳ Proxmox API client helper (wrap `proxmoxer.ProxmoxAPI` with SSL verify option).
- ⏳ Command router reading `GARM_COMMAND` / `GARM_PROVIDER_CONFIG_FILE`; structured logging.

### Phase 2 — Instance lifecycle (MVP)
- ⏳ `ListInstances`: filter by `GARM_POOL_ID` tag.
- ⏳ `GetInstance`: status + IP discovery.
- ⏳ `CreateInstance`:
  - Clone from template VMID when configured; otherwise create VM with cloud-init drive.
  - Apply defaults/overrides (cores, memory, disk, bridge, storage).
  - Tag with `GARM_CONTROLLER_ID` and `GARM_POOL_ID`.
  - Render cloud-init user-data with runner bootstrap (labels, callback URL/token).
  - Start VM and return `Instance` JSON.
- ⏳ `DeleteInstance`: stop and destroy VMID; no-op if missing.

### Phase 3 — Lifecycle polish
- ⏳ `Start` / `Stop`: VM power control by VMID.
- ⏳ `RemoveAllInstances`: delete VMs tagged with controller ID.
- ⏳ Harden tag/notes format to be cluster-safe; ensure idempotency on retries.

### Phase 4 — Quality & packaging
- ⏳ Add minimal smoke tests (mocked proxmoxer) for each command.
- ⏳ Optional linting hooks (`ruff`, `mypy`) and formatting.
- ⏳ Validate `uv build` and console script packaging.

## Task Board (high-level)
| Task | Owner | Status | Notes |
| --- | --- | --- | --- |
| CLI skeleton with env dispatch (`click`) | @assistant | ⏳ | map commands to handlers; propagate exit codes |
| Config loader (TOML) + schema | @assistant | ⏳ | include SSL verify, template VMID, defaults |
| Proxmox client wrapper | @assistant | ⏳ | thin wrapper over `proxmoxer.ProxmoxAPI` |
| List/Get implementations | @assistant | ⏳ | include tag filtering, IP collection |
| Create flow (clone + cloud-init) | @assistant | ⏳ | render user-data from bootstrap payload |
| Delete/Start/Stop | @assistant | ⏳ | handle missing VM as success for delete |
| RemoveAllInstances | @assistant | ⏳ | filter by controller tag |
| Tests & packaging | @assistant | ⏳ | mocked API; `uv build` sanity check |

## Cloud-init & runner bootstrap (draft)
- Create `runner` user with SSH key from config (optional).
- Download runner tarball per `os_type`/`arch` from bootstrap tools list.
- Register using bootstrap token/metadata URLs; set labels including `runner-controller-id` and `runner-pool-id`.
- Install systemd service for persistent runner.

## Config expectations (summary)
- `[pve]`: `host`, `user`, `token_name`, `token_value`, `verify_ssl`.
- `[defaults]`: `node`, `storage`, `pool`, `template_vmid` (optional), `cores`, `memory_mb`, `bridge`, `ssh_public_key` (optional).
- Allow per-pool overrides via `extra_specs` mapping (e.g., `cores`, `memory_mb`, `node`).

## Definition of Done (MVP)
- Running `GARM_COMMAND=ListInstances garm-proxmox-provider` works against a PVE with valid config.
- `CreateInstance` provisions a VM, tags it, installs runner, and returns an `Instance` JSON with `provider_id` set to VMID.
- `DeleteInstance` cleans up without leaking disks/VMs.
- All commands return proper exit codes and JSON where required.
- Package builds with `uv` and exports the console script.