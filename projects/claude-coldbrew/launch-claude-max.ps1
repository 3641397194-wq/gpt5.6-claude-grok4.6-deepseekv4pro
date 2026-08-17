[CmdletBinding()]
param([string[]]$ClaudeArgs)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'Python 3 is required.' }
$args = @((Join-Path $root 'app\claude_pojia.py'), 'launch', '--yes', '--bypass-permissions')
foreach ($item in $ClaudeArgs) { $args += @('--claude-arg', $item) }
& $python.Source @args
exit $LASTEXITCODE
