"""Tests for cloud_init user-data rendering (Linux/Windows × GitHub/Gitea)."""

from __future__ import annotations

import pytest

from garm_proxmox_provider.cloud_init import _is_gitea, render_userdata
from garm_proxmox_provider.config import DefaultsConfig
from garm_proxmox_provider.models import BootstrapInstance


def _defaults(**kwargs) -> DefaultsConfig:
    base = dict(node="pve1", template_vmid=9000)
    base.update(kwargs)
    return DefaultsConfig(**base)


def _bootstrap(**kwargs) -> BootstrapInstance:
    base = dict(
        name="runner-test",
        tools=[],
        repo_url="https://github.com/myorg/myrepo",
        metadata_url="https://garm.example.com/api/v1/metadata",
        callback_url="https://garm.example.com/api/v1/instances/callback",
        instance_token="tok-abc123",
        pool_id="pool-111",
        controller_id="ctrl-222",
        os_type="linux",
        os_arch="amd64",
        labels=["self-hosted", "linux"],
    )
    base.update(kwargs)
    return BootstrapInstance(**base)


# ---------------------------------------------------------------------------
# _is_gitea detection
# ---------------------------------------------------------------------------


def test_is_gitea_by_url() -> None:
    b = _bootstrap(repo_url="https://gitea.example.com/org/repo")
    assert _is_gitea(b) is True


def test_is_github_by_url() -> None:
    b = _bootstrap(repo_url="https://github.com/org/repo")
    assert _is_gitea(b) is False


def test_is_gitea_explicit_extra_spec() -> None:
    b = _bootstrap(extra_specs={"forge_type": "gitea"})
    assert _is_gitea(b) is True


def test_is_forgejo_explicit_extra_spec() -> None:
    b = _bootstrap(extra_specs={"forge_type": "forgejo"})
    assert _is_gitea(b) is True


def test_is_github_explicit_extra_spec_overrides_url() -> None:
    """An explicit forge_type=github on a non-github URL → not Gitea."""
    b = _bootstrap(
        repo_url="https://gitea.example.com/org/repo",
        extra_specs={"forge_type": "github"},
    )
    assert _is_gitea(b) is False


# ---------------------------------------------------------------------------
# Linux / GitHub
# ---------------------------------------------------------------------------


def test_linux_github_cloud_config_header() -> None:
    b = _bootstrap()
    ud = render_userdata(b, "1001", _defaults())
    assert ud.startswith("#cloud-config")


def test_linux_github_contains_config_sh() -> None:
    b = _bootstrap()
    ud = render_userdata(b, "1001", _defaults())
    assert "./config.sh" in ud
    assert "--url 'https://github.com/myorg/myrepo'" in ud
    assert "--name 'runner-test'" in ud
    assert "--labels 'self-hosted,linux'" in ud


def test_linux_github_contains_callback() -> None:
    b = _bootstrap()
    ud = render_userdata(b, "1001", _defaults())
    assert "callback_url" not in ud  # placeholder replaced
    assert "https://garm.example.com/api/v1/instances/callback" in ud
    assert '"provider_id":"1001"' in ud


def test_linux_github_contains_token_fetch() -> None:
    b = _bootstrap()
    ud = render_userdata(b, "1001", _defaults())
    assert "runner-registration-token" in ud
    assert "tok-abc123" in ud


def test_linux_github_no_download_steps() -> None:
    """The slimmed script must not contain any tarball download logic."""
    b = _bootstrap()
    ud = render_userdata(b, "1001", _defaults())
    assert "curl" in ud  # still uses curl for token/callback
    assert "tar xzf" not in ud
    assert "apt-get" not in ud


def test_linux_github_svc_sh_start() -> None:
    b = _bootstrap()
    ud = render_userdata(b, "1001", _defaults())
    assert "./svc.sh start" in ud


def test_linux_github_ssh_key_injected() -> None:
    b = _bootstrap()
    ud = render_userdata(b, "1001", _defaults(ssh_public_key="ssh-ed25519 AAAA test@h"))
    assert "ssh_authorized_keys" in ud
    assert "ssh-ed25519 AAAA test@h" in ud


# ---------------------------------------------------------------------------
# Linux / Gitea
# ---------------------------------------------------------------------------


def test_linux_gitea_uses_act_runner() -> None:
    b = _bootstrap(repo_url="https://gitea.example.com/org/repo")
    ud = render_userdata(b, "1001", _defaults())
    assert "act_runner" in ud
    assert "./act_runner register" in ud
    assert "--instance 'https://gitea.example.com/org/repo'" in ud
    assert "--no-interactive" in ud


def test_linux_gitea_systemctl_start() -> None:
    b = _bootstrap(repo_url="https://gitea.example.com/org/repo")
    ud = render_userdata(b, "1001", _defaults())
    assert "systemctl start act_runner" in ud


def test_linux_gitea_no_config_sh() -> None:
    b = _bootstrap(repo_url="https://gitea.example.com/org/repo")
    ud = render_userdata(b, "1001", _defaults())
    assert "config.sh" not in ud


# ---------------------------------------------------------------------------
# Windows / GitHub (cloudbase-init)
# ---------------------------------------------------------------------------


def test_windows_github_ps1_sysnative_header() -> None:
    b = _bootstrap(os_type="windows")
    ud = render_userdata(b, "2001", _defaults())
    assert ud.startswith("#ps1_sysnative")


def test_windows_github_config_cmd() -> None:
    b = _bootstrap(os_type="windows")
    ud = render_userdata(b, "2001", _defaults())
    assert "config.cmd" in ud
    assert "$RepoUrl" in ud
    assert "$RunnerToken" in ud
    assert "$RunnerName" in ud
    assert "$RunnerLabels" in ud


def test_windows_github_svc_cmd_start() -> None:
    b = _bootstrap(os_type="windows")
    ud = render_userdata(b, "2001", _defaults())
    assert "svc.cmd start" in ud


def test_windows_github_callback() -> None:
    b = _bootstrap(os_type="windows")
    ud = render_userdata(b, "2001", _defaults())
    assert "Invoke-RestMethod" in ud
    assert "$ProviderId" in ud
    assert "$RunnerName" in ud


def test_windows_github_provider_id_substituted() -> None:
    b = _bootstrap(os_type="windows")
    ud = render_userdata(b, "2001", _defaults())
    assert "2001" in ud
    assert "{provider_id}" not in ud


def test_windows_github_no_bash_shebang() -> None:
    b = _bootstrap(os_type="windows")
    ud = render_userdata(b, "2001", _defaults())
    assert "#!/bin/bash" not in ud


# ---------------------------------------------------------------------------
# Windows / Gitea
# ---------------------------------------------------------------------------


def test_windows_gitea_act_runner_exe() -> None:
    b = _bootstrap(
        os_type="windows",
        repo_url="https://gitea.example.com/org/repo",
    )
    ud = render_userdata(b, "2001", _defaults())
    assert "act_runner.exe" in ud
    assert "--instance $RepoUrl" in ud
    assert "--no-interactive" in ud


def test_windows_gitea_start_service() -> None:
    b = _bootstrap(
        os_type="windows",
        repo_url="https://gitea.example.com/org/repo",
    )
    ud = render_userdata(b, "2001", _defaults())
    assert "Start-Service act_runner" in ud


def test_windows_gitea_no_config_cmd() -> None:
    b = _bootstrap(
        os_type="windows",
        repo_url="https://gitea.example.com/org/repo",
    )
    ud = render_userdata(b, "2001", _defaults())
    assert "config.cmd" not in ud


# ---------------------------------------------------------------------------
# Labels fallback to pool_id when no labels provided
# ---------------------------------------------------------------------------


def test_linux_labels_fallback_to_pool_id() -> None:
    b = _bootstrap(labels=[])
    ud = render_userdata(b, "1001", _defaults())
    assert "--labels 'pool-111'" in ud


def test_windows_labels_fallback_to_pool_id() -> None:
    b = _bootstrap(os_type="windows", labels=[])
    ud = render_userdata(b, "2001", _defaults())
    assert "$RunnerLabels = 'pool-111'" in ud
