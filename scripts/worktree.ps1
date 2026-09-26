# Create or remove a lane worktree at %USERPROFILE%\dev\gridlock-wt\<lane> on branch wt/<lane>. ASCII only.
# Usage:  scripts\worktree.ps1 -Lane data            (create from main)
#         scripts\worktree.ps1 -Lane data -From g3   (create from a tag or commit; frozen judge copies)
#         scripts\worktree.ps1 -Lane data -Remove    (remove the worktree; the branch is kept)
param(
  [Parameter(Mandatory = $true)][string]$Lane,
  [string]$From = 'main',
  [switch]$Remove
)
$ErrorActionPreference = 'Stop'
$repo = Join-Path $env:USERPROFILE 'dev\gridlock'
$name = $Lane.ToLower()
$path = Join-Path $env:USERPROFILE ('dev\gridlock-wt\' + $name)
$branch = 'wt/' + $name
if ($Remove) {
  git -C $repo worktree remove $path
  Write-Output ("removed {0} (branch {1} kept)" -f $path, $branch)
  return
}
$exists = git -C $repo branch --list $branch
if ($exists) {
  git -C $repo worktree add $path $branch
} else {
  git -C $repo worktree add $path -b $branch $From
}
Write-Output ("worktree {0} on {1}" -f $path, $branch)
