#!/bin/bash
export METADATA_URL="{{ .MetadataURL }}"
export CALLBACK_URL="{{ .CallbackURL }}"
export BEARER_TOKEN="{{ .CallbackToken }}"
export REPO_URL="{{ .RepoURL }}"
export RUNNER_NAME="{{ .RunnerName }}"
export RUNNER_LABELS="{{ .RunnerLabels }}"
export FORGE_TYPE="{{ if .GitHubRunnerGroup }}github{{ else }}gitea{{ end }}"
export AGENT_MODE="{{ if .AgentMode }}true{{ else }}false{{ end }}"
export AGENT_URL="{{ .AgentURL }}"
export AGENT_TOKEN="{{ .AgentToken }}"
export AGENT_SHELL="{{ .AgentShell }}"

# Trigger the pre-installed script
bash /opt/garm/scripts/startup-linux.sh
