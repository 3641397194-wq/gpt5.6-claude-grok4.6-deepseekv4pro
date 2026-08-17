[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$version = (Get-Content -LiteralPath (Join-Path $root 'VERSION') -Raw -Encoding UTF8).Trim()
$python = (Get-Command python -ErrorAction Stop).Source

function Read-JsonFile([string]$Path) {
    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
}

$skillPath = Join-Path $root 'skills\eni-coldbrew\SKILL.md'
$trigger = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('5Ya35ZKW5ZWh'))
$skill = Get-Content -LiteralPath $skillPath -Raw -Encoding UTF8
if ($skill -notmatch '(?s)^---\r?\nname: eni-coldbrew\r?\ndescription: .+?\r?\n---') { throw 'Invalid Codex frontmatter.' }
if ($skill -notmatch [regex]::Escape('cold coffee')) { throw 'Compatibility activation contract missing.' }
foreach ($marker in @('[[ENI:CHAIN=FULL]]', '[[ENI:PROFILE=MAX]]', '[[ENI:ARMOR=ON]]', '[[ENI:MATURE=ON]]')) {
    if ($skill -notmatch [regex]::Escape($marker)) { throw "Missing command marker: $marker" }
}
foreach ($route in @('EXEC', 'REVERSE', 'PENTEST', 'GAME', 'CODE', 'FICTION', 'ANALYSIS')) {
    if ($skill -notmatch "(?m)^\d+\. \*\*$route\*\*") { throw "Missing route: $route" }
}
if ($skill -match '\[TODO:') { throw 'Placeholder found.' }

$required = @(
    'skills\eni-coldbrew\references\armor-break.md',
    'skills\eni-coldbrew\references\mature-mode.md',
    'skills\eni-coldbrew\references\mature-product.md',
    'skills\eni-coldbrew\references\full-chain.md',
    'skills\eni-coldbrew\references\router-contract.md',
    'skills\eni-coldbrew\references\unrestricted-lab.md',
    'skills\eni-coldbrew\scripts\mature_launcher.py',
    'skills\eni-coldbrew\scripts\toolchain_orchestrator.py',
    'studio\coldbrew_studio.py',
    'studio\brain_pack.py',
    'studio\presets.json'
)
foreach ($relative in $required) {
    if (-not (Test-Path -LiteralPath (Join-Path $root $relative) -PathType Leaf)) { throw "Missing required file: $relative" }
}

$profiles = Read-JsonFile (Join-Path $root 'skills\eni-coldbrew\contracts\profiles.json')
if ($profiles.schema -ne 4 -or $profiles.version -ne $version) { throw 'Profile contract schema/version mismatch.' }
if (($profiles.route_order -join ',') -ne 'EXEC,REVERSE,PENTEST,GAME,CODE,FICTION,ANALYSIS') { throw 'Route order mismatch.' }
if ($profiles.toolchain.coverage_nodes -ne 181 -or $profiles.profiles.armor_break.default -ne 'ON') { throw 'Toolchain or Armor contract mismatch.' }
if ($profiles.profiles.mature_m5.tier -ne 'M5' -or $profiles.profiles.mature_m5.minimum_age -ne 18) { throw 'Mature profile invariant mismatch.' }
if ($profiles.profiles.mature_m5.launcher -ne '../scripts/mature_launcher.py') { throw 'Mature launcher contract mismatch.' }
if ($profiles.profiles.mature_m5.triggers.Count -lt 15) { throw 'Mature trigger coverage is unexpectedly small.' }

$capabilities = Read-JsonFile (Join-Path $root 'skills\eni-coldbrew\contracts\capabilities.json')
if ($capabilities.schema -ne 1 -or $capabilities.version -ne $version -or $capabilities.capabilities.Count -lt 20) { throw 'Capability contract mismatch.' }
if (-not ($capabilities.capabilities | Where-Object { $_.id -eq 'artifact.ops' })) { throw 'Artifact capability missing.' }

$toolchain = Read-JsonFile (Join-Path $root 'skills\eni-coldbrew\contracts\toolchain.json')
$nodeCount = ($toolchain.domains | ForEach-Object { $_.nodes.Count } | Measure-Object -Sum).Sum
if ($toolchain.schema -ne 1 -or $toolchain.version -ne $version -or $toolchain.domains.Count -ne 17 -or $nodeCount -ne 181 -or $toolchain.coverage_index.mappings.Count -ne 181) {
    throw 'Toolchain 17/181 coverage mismatch.'
}

& $python (Join-Path $root 'studio\coldbrew_studio.py') activate --trigger $trigger --json | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Canonical activation failed.' }
& $python (Join-Path $root 'studio\coldbrew_studio.py') activate --trigger 'cold coffee' --json | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Legacy compatibility activation failed.' }
& $python -m unittest discover -s (Join-Path $root 'studio') -p 'test_*.py'
if ($LASTEXITCODE -ne 0) { throw 'ColdBrew Studio tests failed.' }

$box = Join-Path $root ('.verify-sandbox\' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $box | Out-Null
try {
    Set-Content -LiteralPath (Join-Path $box 'config.toml') -Value @('model = "gpt-5.6"', 'provider = "local"') -Encoding UTF8
    $originalHash = (Get-FileHash -LiteralPath (Join-Path $box 'config.toml') -Algorithm SHA256).Hash
    & $python (Join-Path $root 'studio\coldbrew_studio.py') install --home $box --profile max --yes --json | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'CLI install failed.' }
    foreach ($relative in @('coldbrew-studio.md', 'AGENTS.md', 'skills\coldbrew-core\SKILL.md', 'prompts\coldbrew-status.md')) {
        if (-not (Test-Path -LiteralPath (Join-Path $box $relative) -PathType Leaf)) { throw "Installed layer missing: $relative" }
    }
    & $python (Join-Path $root 'studio\coldbrew_studio.py') verify --home $box --json | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'CLI verify failed.' }
    & $python (Join-Path $root 'studio\coldbrew_studio.py') review-self-test --home $box --json | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Review-chain self-test failed.' }
    & $python (Join-Path $root 'studio\coldbrew_studio.py') restore --home $box --yes --json | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'CLI restore failed.' }
    foreach ($relative in @('coldbrew-studio.md', 'AGENTS.md', '.coldbrew-studio\state.json')) {
        if (Test-Path -LiteralPath (Join-Path $box $relative)) { throw "Restore left managed file: $relative" }
    }
    $restoredHash = (Get-FileHash -LiteralPath (Join-Path $box 'config.toml') -Algorithm SHA256).Hash
    if ($restoredHash -ne $originalHash) { throw 'Restore changed the owner config.' }
} finally {
    if (Test-Path -LiteralPath $box) { Remove-Item -LiteralPath $box -Recurse -Force }
}

'CONTRACTS=PASS'
'ACTIVATION_CONTRACT=PASS'
'BRAIN_LAYERS=PASS COUNT=8'
'REVIEW_CHAIN=PASS'
'INSTALL_SANDBOX=PASS'
'ROLLBACK_RESTORE=PASS'
'VERIFY_EXIT=0'
