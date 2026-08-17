[CmdletBinding()]
param(
    [string]$CodexHome,
    [string]$Profile = 'max'
)

$ErrorActionPreference = 'Stop'
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'Python 3 is required to launch ColdBrew Studio.' }

$arguments = @((Join-Path $PSScriptRoot 'studio\coldbrew_studio.py'), 'gui', '--profile', $Profile)
if ($CodexHome) { $arguments += @('--home', $CodexHome) }
& $python.Source @arguments
exit $LASTEXITCODE
