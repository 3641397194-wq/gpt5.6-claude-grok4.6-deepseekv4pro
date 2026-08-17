[CmdletBinding()]
param(
    [ValidateSet('user','project')]
    [string]$Scope = 'user',
    [string]$Project
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'Python 3 is required.' }
$args = @((Join-Path $root 'app\claude_pojia.py'), 'restore', '--scope', $Scope)
if ($Project) { $args += @('--project', $Project) }
& $python.Source @args
exit $LASTEXITCODE
