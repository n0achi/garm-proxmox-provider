#!/bin/bash
set -e

echo "Registering lean Proxmox templates into GARM..."

# Register Linux GitHub template
garm-cli template create \
    --name "proxmox-linux-github" \
    --os-type "linux" \
    --forge-type "github" \
    --description "Lean Proxmox template for Linux GitHub runners" \
    --path "/opt/garm/templates/linux-custom-script.sh" || echo "Template might already exist."

# Register Linux Gitea template
garm-cli template create \
    --name "proxmox-linux-gitea" \
    --os-type "linux" \
    --forge-type "gitea" \
    --description "Lean Proxmox template for Linux Gitea runners" \
    --path "/opt/garm/templates/linux-custom-script.sh" || echo "Template might already exist."

# Register Windows GitHub template
garm-cli template create \
    --name "proxmox-windows-github" \
    --os-type "windows" \
    --forge-type "github" \
    --description "Lean Proxmox template for Windows GitHub runners" \
    --path "/opt/garm/templates/windows-custom-script.ps1" || echo "Template might already exist."

# Register Windows Gitea template
garm-cli template create \
    --name "proxmox-windows-gitea" \
    --os-type "windows" \
    --forge-type "gitea" \
    --description "Lean Proxmox template for Windows Gitea runners" \
    --path "/opt/garm/templates/windows-custom-script.ps1" || echo "Template might already exist."

echo "Done!"
