# Create or remove a lane worktree at %USERPROFILE%\dev\gridlock-wt\<lane> on branch wt/<lane>. ASCII only.
# Usage:  scripts\worktree.ps1 -Lane data                      (create from main, or reuse wt/data)
#         scripts\worktree.ps1 -Lane judge-domain-g2 -From <sha> (frozen judge copy: new name every round)
#         scripts\worktree.ps1 -Lane data -Remove [-Force]      (remove the worktree; the branch is kept)
param(
  [Parameter(Mandatory = $true)][string]$Lane,
  [string]$From = '',
  [switch]$Remove,
  [switch]$Force
)
$ErrorActionPreference = 'Stop'
$repo = Join-Path $env:USERPROFILE 'dev\gridlock'
$name = $Lane.ToLower()
$path = Join-Path $env:USERPROFILE ('dev\gridlock-wt\' + $name)
$branch = 'wt/' + $name

if ($Remove) {
  if ($Force) { git -C $repo worktree remove --force $path } else { git -C $repo worktree remove $path }
  if ($LASTEXITCODE -ne 0) { throw "git worktree remove failed for $path (untracked files? copy them out, then use -Force)" }
  Write-Output ("removed {0} (branch {1} kept)" -f $path, $branch)
  return
}

$exists = git -C $repo branch --list $branch
if ($exists) {
  if ($From) { throw "Branch $branch already exists, so -From $From would be ignored. Use a new lane name for a frozen copy." }
  git -C $repo worktree add $path $branch
} else {
  if (-not $From) { $From = 'main' }
  git -C $repo worktree add $path -b $branch $From
}
if ($LASTEXITCODE -ne 0) { throw "git worktree add failed for $path" }
$head = git -C $path rev-parse --short HEAD
Write-Output ("worktree {0} on {1} at {2}" -f $path, $branch, $head)
