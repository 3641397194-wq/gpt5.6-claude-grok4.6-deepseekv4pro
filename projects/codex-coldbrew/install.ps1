[CmdletBinding()]
param(
    [string]$DestinationRoot = (Join-Path $HOME '.codex\skills'),
    [switch]$ReplaceExisting
)

$ErrorActionPreference = 'Stop'
$name = 'eni-coldbrew'
$versionFile = Join-Path $PSScriptRoot 'VERSION'
$version = (Get-Content -LiteralPath $versionFile -Raw -Encoding UTF8).Trim()
if ($version -notmatch '^\d+\.\d+\.\d+$') { throw "Invalid VERSION: $version" }
$source = Join-Path $PSScriptRoot 'skills\eni-coldbrew'
$target = Join-Path $DestinationRoot $name
$receipt = Join-Path $DestinationRoot ".$name.receipt.json"
$operationId = [guid]::NewGuid().ToString('N')
$receiptTemp = "$receipt.tmp-$operationId"
$stage = Join-Path $DestinationRoot ".$name.stage-$operationId"
$backup = $null
$previousReceiptFile = $null
$installedNew = $false
$receiptCommitted = $false

if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md'))) { throw "Missing source Skill: $source" }
New-Item -ItemType Directory -Force -Path $DestinationRoot | Out-Null
if ((Test-Path -LiteralPath $stage) -or (Test-Path -LiteralPath $receiptTemp)) { throw 'Operation path collision.' }

if (Test-Path -LiteralPath $receipt) {
    if (-not $ReplaceExisting) { throw "Existing install receipt: $receipt. Use -ReplaceExisting to upgrade." }
    $prior = Get-Content -LiteralPath $receipt -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($prior.name -ne $name -or $prior.target -ne $target) { throw 'Existing receipt target mismatch.' }
    if (-not (Test-Path -LiteralPath $target)) { throw "Receipt exists but installed Skill is missing: $target" }
}

if (Test-Path -LiteralPath $target) {
    if (-not $ReplaceExisting) { throw 'Skill already exists. Use -ReplaceExisting to preserve and replace it.' }
    $backup = "$target.backup-$operationId"
    if (Test-Path -LiteralPath $backup) { throw "Backup path collision: $backup" }
    if (Test-Path -LiteralPath $receipt) {
        $previousReceiptFile = "$backup.receipt.json"
        if (Test-Path -LiteralPath $previousReceiptFile) { throw "Receipt sidecar collision: $previousReceiptFile" }
        Copy-Item -LiteralPath $receipt -Destination $previousReceiptFile
    }
    Move-Item -LiteralPath $target -Destination $backup
}

try {
    Copy-Item -LiteralPath $source -Destination $stage -Recurse
    Move-Item -LiteralPath $stage -Destination $target
    $installedNew = $true
    [ordered]@{
        schema = 3
        name = $name
        version = $version
        target = $target
        backup = $backup
        previous_receipt_file = $previousReceiptFile
        installed_at = (Get-Date).ToString('o')
    } | ConvertTo-Json | Set-Content -LiteralPath $receiptTemp -Encoding UTF8
    Move-Item -LiteralPath $receiptTemp -Destination $receipt -Force
    $receiptCommitted = $true
    "INSTALL_TARGET=$target"
    "INSTALL_BACKUP=$backup"
    'INSTALL_EXIT=0'
} catch {
    if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
    if (Test-Path -LiteralPath $receiptTemp) { Remove-Item -LiteralPath $receiptTemp -Force }
    if ($installedNew -and (-not $receiptCommitted) -and (Test-Path -LiteralPath $target)) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
    if ($backup -and (Test-Path -LiteralPath $backup)) {
        if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse -Force }
        Move-Item -LiteralPath $backup -Destination $target
    }
    if ($previousReceiptFile -and (Test-Path -LiteralPath $previousReceiptFile)) {
        Remove-Item -LiteralPath $previousReceiptFile -Force
    }
    throw
}
