# Launch (or resume) a Codex session with a brief file on stdin. ASCII only.
# Usage:  scripts\codex-lead.ps1 -Brief reviews\2026-09-26-gridlock-build\MISSION.md
#         scripts\codex-lead.ps1 -Brief <corrections.md> -ResumeId <session id>
#         add -WhatIf to print the command without running it
#         -Model / -Effort pick another subscription model (default gpt-6-sol at high reasoning)
# The brief goes to stdin as a file handle (PowerShell 5.1 would re-encode a piped string).
param(
  [Parameter(Mandatory = $true)][string]$Brief,
  [string]$Name = 'lead',
  [string]$Repo = (Join-Path $env:USERPROFILE 'dev\gridlock'),
  [string]$Port = '8770',
  [string]$ResumeId = '',
  [string]$Model = 'gpt-6-sol',
  [ValidateSet('low', 'medium', 'high', 'xhigh')][string]$Effort = 'high',
  [switch]$WhatIf
)
$ErrorActionPreference = 'Stop'
$dev = Join-Path $env:USERPROFILE 'dev'
$runs = Join-Path $dev 'gridlock-runs'
$wt = Join-Path $dev 'gridlock-wt'
# Codex's sandbox keeps any folder named .git read-only, so the clone keeps its git data here
# (created with: git init --separate-git-dir). It must be writable for branches, worktrees and commits.
$gitdir = Join-Path $dev 'gridlock-git'
$codex = Join-Path $env:LOCALAPPDATA 'Programs\OpenAI\Codex\bin\codex.exe'
if (-not (Test-Path $codex)) { throw "Codex CLI not found at $codex" }
if (-not (Test-Path $Brief)) { throw "Brief not found: $Brief" }
$Brief = (Resolve-Path $Brief).Path
New-Item -ItemType Directory -Force (Join-Path $runs 'codex') | Out-Null
New-Item -ItemType Directory -Force $wt | Out-Null

$env:GRIDLOCK_PY = Join-Path $dev 'gridlock-venv\Scripts\python.exe'
$env:GRIDLOCK_AI = 'off'
$env:GRIDLOCK_TEST_PORT = $Port
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $dev 'ms-playwright'
$env:PSExecutionPolicyPreference = 'Bypass'
# Codex must never inherit the launching Claude session's credentials or session variables.
Get-ChildItem Env: | Where-Object { $_.Name -match '^(ANTHROPIC_|CLAUDE_|CLAUDECODE$|USE_.*OAUTH)' } |
  ForEach-Object { Remove-Item -LiteralPath ('Env:' + $_.Name) }

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$jsonl = Join-Path $runs ("codex\{0}-{1}.jsonl" -f $stamp, $Name)
$errf = Join-Path $runs ("codex\{0}-{1}.stderr.txt" -f $stamp, $Name)
$last = Join-Path $runs ("{0}-last.md" -f $Name)

# Values without quotes: Codex parses them as TOML and falls back to a literal string.
$common = @('-m', $Model, '-c', "model_reasoning_effort=$Effort", '-c', 'approval_policy=never',
            '--enable', 'prevent_idle_sleep', '--json', '-o', $last)
if ($ResumeId) {
  # exec resume takes no -s/--add-dir, so the sandbox and writable roots go in as config (TOML literal strings).
  $roots = "sandbox_workspace_write.writable_roots=['{0}','{1}','{2}']" -f $wt, $runs, $gitdir
  $argv = @('exec', 'resume', $ResumeId, '-c', 'sandbox_mode=workspace-write', '-c', $roots) + $common + @('-')
} else {
  $argv = @('exec', '-C', $Repo, '-s', 'workspace-write', '--add-dir', $wt, '--add-dir', $runs, '--add-dir', $gitdir) + $common + @('-')
}

if ($WhatIf) {
  Write-Output ("{0} {1}  <{2}  >{3}" -f $codex, ($argv -join ' '), $Brief, $jsonl)
  return
}

$started = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
# Wait on the Codex process only: Start-Process -Wait would also wait for any server or browser a
# sub-agent left running, and the completion notice would never arrive.
$p = Start-Process -FilePath $codex -ArgumentList $argv -WorkingDirectory $Repo `
  -RedirectStandardInput $Brief -RedirectStandardOutput $jsonl -RedirectStandardError $errf `
  -NoNewWindow -PassThru
$null = $p.Handle
$p.WaitForExit()

$sid = ''
foreach ($line in (Get-Content $jsonl -Encoding UTF8)) {
  if ($line -match '"thread_id"\s*:\s*"([^"]+)"') { $sid = $Matches[1]; break }
}
Write-Output ("started={0} ended={1} exit={2} session={3}" -f $started, (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $p.ExitCode, $sid)
Write-Output ("jsonl={0}" -f $jsonl)
Write-Output ("last={0}" -f $last)
