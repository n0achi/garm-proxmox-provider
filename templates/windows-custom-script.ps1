#ps1_sysnative
$env:METADATA_URL = "{{ .MetadataURL }}"
$env:CALLBACK_URL = "{{ .CallbackURL }}"
$env:BEARER_TOKEN = "{{ .CallbackToken }}"
$env:REPO_URL = "{{ .RepoURL }}"
$env:RUNNER_NAME = "{{ .RunnerName }}"
$env:RUNNER_LABELS = "{{ .RunnerLabels }}"
$env:FORGE_TYPE = "{{ if .GitHubRunnerGroup }}github{{ else }}gitea{{ end }}"
$env:AGENT_MODE = "{{ if .AgentMode }}true{{ else }}false{{ end }}"
$env:AGENT_URL = "{{ .AgentURL }}"
$env:AGENT_TOKEN = "{{ .AgentToken }}"
$env:AGENT_SHELL = "{{ .AgentShell }}"

# Trigger the pre-installed script
& C:\garm\scripts\startup-windows.ps1
