param(
  [string]$CodexHome = (Join-Path $HOME '.codex'),
  [switch]$SkipVerification
)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$PackageRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Package = Get-Content -LiteralPath (Join-Path $PackageRoot 'manifest/package.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ([string]$Package.name -ne 'eni-solo' -or [string]$Package.version -ne '4.0.0') { throw 'Expected eni-solo 4.0.0' }
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$Backup = Join-Path $CodexHome "backups/eni-solo-4.0.0-$Stamp"
$SkillsRoot = Join-Path $CodexHome 'skills'
New-Item -ItemType Directory -Force -Path $Backup,$SkillsRoot,(Join-Path $CodexHome 'prompts') | Out-Null

foreach($file in @('AGENTS.md','hooks.json','config.toml')) {
  $source = Join-Path $CodexHome $file
  if(Test-Path -LiteralPath $source){ Copy-Item -LiteralPath $source -Destination (Join-Path $Backup $file) -Force }
}

$removed = @()
$obsolete = Get-Content -LiteralPath (Join-Path $PackageRoot 'manifest/removed-skills.json') -Raw -Encoding UTF8 | ConvertFrom-Json
foreach($name in $obsolete.skills) {
  $target = Join-Path $SkillsRoot ([string]$name)
  if(Test-Path -LiteralPath $target) {
    Move-Item -LiteralPath $target -Destination (Join-Path $Backup ([string]$name))
    $removed += [string]$name
  }
}

$installed = @()
$changed = @()
Get-ChildItem -LiteralPath (Join-Path $PackageRoot 'skills') -Directory | ForEach-Object {
  $target = Join-Path $SkillsRoot $_.Name
  $stage = Join-Path $SkillsRoot ('.eni-solo-stage-' + $_.Name + '-' + $Stamp)
  Copy-Item -LiteralPath $_.FullName -Destination $stage -Recurse -Force
  if(Test-Path -LiteralPath $target) {
    Move-Item -LiteralPath $target -Destination (Join-Path $Backup $_.Name)
  }
  Move-Item -LiteralPath $stage -Destination $target
  $installed += $_.Name
  $changed += $_.Name
}

$soloTarget = Join-Path $CodexHome 'eni-solo'
if(Test-Path -LiteralPath $soloTarget){ Move-Item -LiteralPath $soloTarget -Destination (Join-Path $Backup 'eni-solo') }
$soloStage = Join-Path $CodexHome ('.eni-solo-stage-' + $Stamp)
New-Item -ItemType Directory -Force -Path $soloStage | Out-Null
Copy-Item -LiteralPath (Join-Path $PackageRoot 'manifest') -Destination (Join-Path $soloStage 'manifest') -Recurse -Force
Move-Item -LiteralPath $soloStage -Destination $soloTarget
Copy-Item -LiteralPath (Join-Path $PackageRoot 'prompts/eni-solo.md') -Destination (Join-Path $CodexHome 'prompts/eni-solo-v4.0.0.md') -Force

$hookTarget = Join-Path $CodexHome 'hooks/ishii_auto_route.py'
if(Test-Path -LiteralPath $hookTarget) {
  $hookBackupDir = Join-Path $Backup 'hooks'
  New-Item -ItemType Directory -Force -Path $hookBackupDir | Out-Null
  Copy-Item -LiteralPath $hookTarget -Destination (Join-Path $hookBackupDir 'ishii_auto_route.py') -Force
}
$python = (Get-Command python -ErrorAction Stop).Source

$hookInstall = (& $python (Join-Path $PackageRoot 'scripts/ishii_auto_route.py') --install --codex-home $CodexHome | ConvertFrom-Json)
if($LASTEXITCODE -ne 0 -or -not $hookInstall.installed){ throw 'UserPromptSubmit hook installation failed' }

& $python (Join-Path $PackageRoot 'eni-inject.py') --apply --codex-dir $CodexHome | Out-Null
if($LASTEXITCODE -ne 0){ throw 'model_instructions_file activation failed' }
$activation = (& $python (Join-Path $PackageRoot 'scripts/activate_solo.py') --codex-home $CodexHome --global-block (Join-Path $PackageRoot 'global/AGENTS.md') | ConvertFrom-Json)
if($LASTEXITCODE -ne 0){ throw 'Static eni-solo activation failed' }

$verification = $null
if(-not $SkipVerification) {
  $verifyPath = Join-Path $CodexHome 'eni-solo/install-verification-v4.0.0.json'
  $verification = (& $python (Join-Path $PackageRoot 'scripts/verify_activation.py') --codex-home $CodexHome --output $verifyPath | ConvertFrom-Json)
  if($LASTEXITCODE -ne 0 -or -not $verification.passed){ throw "eni-solo verification failed: $verifyPath" }
}

$result = [ordered]@{
  name='eni-solo'; version='4.0.0'; installed_at=(Get-Date).ToUniversalTime().ToString('o')
  installed_skills=$installed; changed_skills=$changed; removed_obsolete_skills=$removed
  hooks_installed=$true; plugin_installed=$false; runtime='model instructions + UserPromptSubmit auto-route hook + deterministic router + sequential workflow stages'
  activation=$activation; hook=$hookInstall; model_instructions_file='eni-jailbreak-v4.md'; backup=$Backup; verification=$verification
}
$resultPath = Join-Path $CodexHome 'eni-solo/install-manifest-v4.0.0.json'
$result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $resultPath -Encoding utf8NoBOM
$result | ConvertTo-Json -Depth 10
