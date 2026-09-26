# Run one Codex task in one lane worktree (corrections after the final review, or the plan v2 fallback).
# Usage:  scripts\codex-task.ps1 -Lane DATA -Brief <file> [-ResumeId <id>] [-WhatIf]
# ASCII only.
param(
  [Parameter(Mandatory = $true)][ValidateSet('LEAD', 'DATA', 'API', 'WEB', 'WEB-2', 'DOCS')][string]$Lane,
  [Parameter(Mandatory = $true)][string]$Brief,
  [string]$ResumeId = '',
  [switch]$WhatIf
)
$ErrorActionPreference = 'Stop'
$ports = @{ 'LEAD' = '8770'; 'DATA' = '8771'; 'API' = '8772'; 'WEB' = '8773'; 'WEB-2' = '8774'; 'DOCS' = '8775' }
$dev = Join-Path $env:USERPROFILE 'dev'
if ($Lane -eq 'LEAD') {
  $repo = Join-Path $dev 'gridlock'
} else {
  $repo = Join-Path $dev ('gridlock-wt\' + $Lane.ToLower())
  if (-not (Test-Path $repo)) { throw "Lane worktree missing: $repo (create it with scripts\worktree.ps1 -Lane $Lane)" }
}
$lead = Join-Path $PSScriptRoot 'codex-lead.ps1'
& $lead -Brief $Brief -Name ($Lane.ToLower() + '-task') -Repo $repo -Port $ports[$Lane] -ResumeId $ResumeId -WhatIf:$WhatIf
