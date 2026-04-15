"""Cloud-init / cloudbase-init user-data renderer for GARM runner bootstrap.

Templates assume the runner binary is already present on the VM image
(installed by the Packer build), along with the startup script at:
  - Linux: /opt/garm/scripts/startup-linux.sh
  - Windows: C:\\garm\\scripts\\startup-windows.ps1

The scripts only handle registration, service start, and status callback.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import ClusterConfig
    from .models import BootstrapInstance

# ---------------------------------------------------------------------------
# Forge detection
# ---------------------------------------------------------------------------


def _is_gitea(bootstrap: BootstrapInstance) -> bool:
    """Return True if the bootstrap targets a Gitea/Forgejo instance."""
    forge_type = bootstrap.extra_specs.get("forge_type", "")
    if forge_type:
        return forge_type.lower() in ("gitea", "forgejo")
    return "github.com" not in bootstrap.repo_url


# ---------------------------------------------------------------------------
# Linux scripts — runner binary pre-installed by Packer image
# ---------------------------------------------------------------------------


def _render_linux_userdata(
    bootstrap: BootstrapInstance,
    provider_id: str,
    defaults: ClusterConfig,
) -> str:
    """Render a bash script for Linux (works with cloud-init and LXC exec)."""
    labels = ",".join(bootstrap.labels) if bootstrap.labels else bootstrap.pool_id
    forge_type = "gitea" if _is_gitea(bootstrap) else "github"

    ssh_setup = ""
    if defaults.ssh_public_key:
        key = defaults.ssh_public_key.strip()
        ssh_setup = f"""\
mkdir -p /home/runner/.ssh
echo "{key}" >> /home/runner/.ssh/authorized_keys
chown -R runner:runner /home/runner/.ssh
chmod 700 /home/runner/.ssh
chmod 600 /home/runner/.ssh/authorized_keys
"""

    return f"""#!/bin/bash
set -euo pipefail

{ssh_setup}
export METADATA_URL="{bootstrap.metadata_url.rstrip("/")}"
export CALLBACK_URL="{bootstrap.callback_url}"
export BEARER_TOKEN="{bootstrap.instance_token}"
export REPO_URL="{bootstrap.repo_url}"
export RUNNER_NAME="{bootstrap.name}"
export RUNNER_LABELS="{labels}"
export FORGE_TYPE="{forge_type}"
export PROVIDER_ID="{provider_id}"

bash /opt/garm/scripts/startup-linux.sh
"""


# ---------------------------------------------------------------------------
# Windows scripts — runner binary pre-installed by Packer image
# cloudbase-init processes #ps1_sysnative as a 64-bit PowerShell script.
# ---------------------------------------------------------------------------


def _render_windows_userdata(
    bootstrap: BootstrapInstance,
    provider_id: str,
) -> str:
    """Render a cloudbase-init PowerShell script for Windows."""
    labels = ",".join(bootstrap.labels) if bootstrap.labels else bootstrap.pool_id
    forge_type = "gitea" if _is_gitea(bootstrap) else "github"

    return f"""\
#ps1_sysnative
$ErrorActionPreference = 'Stop'

$env:METADATA_URL = "{bootstrap.metadata_url.rstrip("/")}"
$env:CALLBACK_URL = "{bootstrap.callback_url}"
$env:BEARER_TOKEN = "{bootstrap.instance_token}"
$env:REPO_URL = "{bootstrap.repo_url}"
$env:RUNNER_NAME = "{bootstrap.name}"
$env:RUNNER_LABELS = "{labels}"
$env:FORGE_TYPE = "{forge_type}"
$env:PROVIDER_ID = "{provider_id}"

& C:\\garm\\scripts\\startup-windows.ps1
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render_userdata(
    bootstrap: BootstrapInstance,
    provider_id: str,
    defaults: ClusterConfig,
) -> str:
    """Return the appropriate user-data document for the bootstrap's OS type."""
    if bootstrap.os_type == "windows":
        return _render_windows_userdata(bootstrap, provider_id)
    return _render_linux_userdata(bootstrap, provider_id, defaults)
