[CmdletBinding()]
param(
    [ValidateSet('user','project')]
    [string]$Scope = 'user',
    [string]$Project,
    [ValidateSet('max-breaker','builder','research','creative')]
    [string]$Profile = 'max-breaker',
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'Python 3 is required. Install Python, then run this installer again.' }
$args = @((Join-Path $root 'app\claude_pojia.py'), 'install', '--scope', $Scope, '--profile', $Profile, '--yes')
if ($Project) { $args += @('--project', $Project) }
if ($Force) { $args += '--force' }
& $python.Source @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host 'Claude 破甲 / 冷咖啡 deployment complete.' -ForegroundColor Green
