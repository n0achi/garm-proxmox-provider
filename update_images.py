#!/usr/bin/env python3
"""
Update Proxmox templates with GARM post-processing scripts natively.
This script clones existing base templates into a unique VMID range (55000+),
starts them, injects and runs the installation scripts via Proxmox API
(LXC exec or QEMU Guest Agent), shuts them down, and turns them into GARM templates.
"""

import argparse
import base64
import logging
import sys
import time
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

from proxmoxer import ProxmoxAPI
from proxmoxer.core import ResourceException

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

GARM_VMID_START = 55000
SCRIPTS_DIR = (
    Path(__file__).parent.parent
    / "runner-images-proxmox"
    / "images"
    / "garm"
    / "scripts"
)


def load_pve_client(config_path: str) -> ProxmoxAPI:
    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)

    pve = cfg.get("pve", {})
    return ProxmoxAPI(
        pve.get("host"),
        user=pve.get("user"),
        token_name=pve.get("token_name"),
        token_value=pve.get("token_value"),
        verify_ssl=pve.get("verify_ssl", False),
    )


def wait_task(prox: ProxmoxAPI, node: str, upid: str, timeout: int = 300) -> None:
    start_time = time.time()
    while time.time() - start_time < timeout:
        task = prox.nodes(node).tasks(upid).status.get()
        if task.get("status") == "stopped":
            if task.get("exitstatus") == "OK":
                return
            raise RuntimeError(f"Task {upid} failed: {task.get('exitstatus')}")
        time.sleep(2)
    raise TimeoutError(f"Task {upid} timed out")


def run_lxc_cmd(prox: ProxmoxAPI, node: str, vmid: int, cmd: list[str]) -> None:
    try:
        prox.nodes(node).lxc(vmid).exec.post(command=cmd)
    except ResourceException as e:
        logger.error(f"LXC exec failed: {e}")
        raise


def run_qemu_cmd(prox: ProxmoxAPI, node: str, vmid: int, cmd: list[str]) -> None:
    # Wait for guest agent
    for _ in range(30):
        try:
            res = prox.nodes(node).qemu(vmid).agent.ping.post()
            break
        except Exception:
            time.sleep(2)
    else:
        raise TimeoutError("QEMU Guest Agent not responding")

    res = prox.nodes(node).qemu(vmid).agent.exec.post(command=cmd)
    pid = res.get("pid")

    for _ in range(60):
        status = prox.nodes(node).qemu(vmid).agent("exec-status").get(pid=pid)
        if status.get("exited", False):
            if status.get("exitcode", 1) != 0:
                err = status.get("err-data", "")
                logger.error(
                    f"Command failed with exit code {status.get('exitcode')}: {err}"
                )
            return
        time.sleep(2)
    raise TimeoutError(f"QEMU command timed out: {cmd}")


def inject_and_install_linux(
    prox: ProxmoxAPI, node: str, vmid: int, is_lxc: bool
) -> None:
    install_sh = (SCRIPTS_DIR / "install-linux.sh").read_text()
    startup_sh = (SCRIPTS_DIR / "startup-linux.sh").read_text()

    install_b64 = base64.b64encode(install_sh.encode()).decode()
    startup_b64 = base64.b64encode(startup_sh.encode()).decode()

    cmds = [
        ["/bin/bash", "-c", "mkdir -p /opt/garm/scripts"],
        [
            "/bin/bash",
            "-c",
            f"echo {install_b64} | base64 -d > /opt/garm/scripts/install-linux.sh",
        ],
        [
            "/bin/bash",
            "-c",
            f"echo {startup_b64} | base64 -d > /opt/garm/scripts/startup-linux.sh",
        ],
        ["/bin/bash", "-c", "chmod +x /opt/garm/scripts/*.sh"],
        ["/bin/bash", "-c", "/opt/garm/scripts/install-linux.sh"],
    ]

    for cmd in cmds:
        if is_lxc:
            run_lxc_cmd(prox, node, vmid, cmd)
            time.sleep(1)  # LXC exec returns immediately; pause briefly
        else:
            run_qemu_cmd(prox, node, vmid, cmd)

    # LXC needs a moment if scripts were detached
    if is_lxc:
        logger.info("Waiting for LXC install script to finish (~30s)...")
        time.sleep(30)


def inject_and_install_windows(prox: ProxmoxAPI, node: str, vmid: int) -> None:
    install_ps1 = (SCRIPTS_DIR / "install-windows.ps1").read_text()
    startup_ps1 = (SCRIPTS_DIR / "startup-windows.ps1").read_text()

    install_b64 = base64.b64encode(install_ps1.encode("utf-16le")).decode()
    startup_b64 = base64.b64encode(startup_ps1.encode("utf-16le")).decode()

    cmds = [
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            "New-Item -ItemType Directory -Force -Path C:\\garm\\scripts",
        ],
        ["powershell.exe", "-NoProfile", "-EncodedCommand", install_b64],
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            f"[System.IO.File]::WriteAllBytes('C:\\garm\\scripts\\startup-windows.ps1', [System.Convert]::FromBase64String('{startup_b64}'))",
        ],
    ]

    for cmd in cmds:
        run_qemu_cmd(prox, node, vmid, cmd)


def process_template(prox: ProxmoxAPI, node: str, tpl: dict, new_vmid: int) -> None:
    base_vmid = tpl["vmid"]
    res_type = tpl["type"]
    base_name = tpl.get("name", f"template-{base_vmid}")
    new_name = f"garm-{base_name}"

    logger.info(
        f"Processing {res_type} template {base_vmid} ({base_name}) -> {new_vmid} ({new_name})"
    )

    # 1. Clone
    logger.info(f"Cloning {base_vmid} to {new_vmid}...")
    if res_type == "lxc":
        upid = (
            prox.nodes(node)
            .lxc(base_vmid)
            .clone.post(newid=new_vmid, hostname=new_name, full=1)
        )
    else:
        upid = (
            prox.nodes(node)
            .qemu(base_vmid)
            .clone.post(newid=new_vmid, name=new_name, full=1)
        )
    wait_task(prox, node, upid)

    # 2. Start
    logger.info(f"Starting {new_vmid}...")
    if res_type == "lxc":
        prox.nodes(node).lxc(new_vmid).status.start.post()
    else:
        prox.nodes(node).qemu(new_vmid).status.start.post()

    time.sleep(10)  # Wait for boot

    # 3. Inject & Install
    logger.info(f"Injecting scripts into {new_vmid}...")
    is_windows = "windows" in base_name.lower() or "win" in base_name.lower()

    try:
        if is_windows and res_type == "qemu":
            inject_and_install_windows(prox, node, new_vmid)
        else:
            inject_and_install_linux(prox, node, new_vmid, is_lxc=(res_type == "lxc"))
    except Exception as e:
        logger.error(f"Failed to inject scripts into {new_vmid}: {e}")
        logger.warning(f"Leaving VM {new_vmid} running for debugging.")
        return

    # 4. Stop
    logger.info(f"Stopping {new_vmid}...")
    if res_type == "lxc":
        upid = prox.nodes(node).lxc(new_vmid).status.stop.post()
    else:
        upid = prox.nodes(node).qemu(new_vmid).status.stop.post()
    wait_task(prox, node, upid)

    # 5. Convert to template
    logger.info(f"Converting {new_vmid} to template...")
    if res_type == "lxc":
        prox.nodes(node).lxc(new_vmid).template.post()
    else:
        prox.nodes(node).qemu(new_vmid).template.post()

    logger.info(f"Success! GARM Template available: {new_name} (VMID {new_vmid})")


def main():
    parser = argparse.ArgumentParser(
        description="Inject GARM scripts into Proxmox Templates natively."
    )
    parser.add_argument(
        "--config",
        default="config/garm-provider-proxmox.toml",
        help="Path to provider TOML",
    )
    parser.add_argument("--node", required=True, help="Proxmox node name (e.g. pve)")
    parser.add_argument(
        "--vmid", type=int, help="Specific base template VMID to process"
    )
    args = parser.parse_args()

    prox = load_pve_client(args.config)
    resources = prox.cluster.resources.get(type="vm")

    templates = [
        r for r in resources if r.get("template") == 1 and r.get("node") == args.node
    ]

    if args.vmid:
        templates = [t for t in templates if t["vmid"] == args.vmid]
        if not templates:
            logger.error(f"Template VMID {args.vmid} not found on node {args.node}")
            sys.exit(1)

    # Filter out already processed GARM templates
    templates = [t for t in templates if not t.get("name", "").startswith("garm-")]

    if not templates:
        logger.info("No base templates found to process.")
        return

    current_vmid = GARM_VMID_START
    existing_vmids = {r["vmid"] for r in resources}

    for tpl in templates:
        while current_vmid in existing_vmids:
            current_vmid += 1

        process_template(prox, args.node, tpl, current_vmid)
        existing_vmids.add(current_vmid)
        current_vmid += 1


if __name__ == "__main__":
    main()
