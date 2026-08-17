[CmdletBinding()]
param([string]$DestinationRoot = (Join-Path $HOME '.codex\skills'))

$ErrorActionPreference = 'Stop'
$name = 'eni-coldbrew'
$target = Join-Path $DestinationRoot $name
$receipt = Join-Path $DestinationRoot ".$name.receipt.json"
if (-not (Test-Path -LiteralPath $receipt)) { throw "Install receipt not found: $receipt" }
$state = Get-Content -LiteralPath $receipt -Raw -Encoding UTF8 | ConvertFrom-Json
if ($state.name -ne $name -or $state.target -ne $target) { throw 'Receipt target mismatch.' }
if ((Split-Path -Leaf $target) -ne $name) { throw "Unsafe target: $target" }

$rootFull = [IO.Path]::GetFullPath($DestinationRoot).TrimEnd('\','/')
if ($state.backup) {
    $backupFull = [IO.Path]::GetFullPath([string]$state.backup)
    if ((Split-Path -Parent $backupFull) -ne $rootFull -or (Split-Path -Leaf $backupFull) -notlike "$name.backup-*") {
        throw "Unsafe backup path: $backupFull"
    }
    if (-not (Test-Path -LiteralPath $backupFull)) { throw "Backup missing: $backupFull" }
}
if ($state.previous_receipt_file) {
    $previousReceiptFull = [IO.Path]::GetFullPath([string]$state.previous_receipt_file)
    if ((Split-Path -Parent $previousReceiptFull) -ne $rootFull -or (Split-Path -Leaf $previousReceiptFull) -notlike "$name.backup-*.receipt.json") {
        throw "Unsafe previous receipt path: $previousReceiptFull"
    }
    if (-not (Test-Path -LiteralPath $previousReceiptFull)) { throw "Previous receipt missing: $previousReceiptFull" }
}

if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse -Force }
if ($state.backup) {
    Move-Item -LiteralPath $backupFull -Destination $target
    "RESTORED_BACKUP=$target"
}

if ($state.previous_receipt_file) {
    Move-Item -LiteralPath $previousReceiptFull -Destination $receipt -Force
    'RESTORED_PREVIOUS_RECEIPT=1'
} elseif ($state.previous_receipt) {
    # Compatibility with schema 2 receipts created by early v3.0.1 builds.
    $receiptTemp = "$receipt.tmp-$([guid]::NewGuid().ToString('N'))"
    $state.previous_receipt | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $receiptTemp -Encoding UTF8
    Move-Item -LiteralPath $receiptTemp -Destination $receipt -Force
    'RESTORED_PREVIOUS_RECEIPT=1'
} else {
    Remove-Item -LiteralPath $receipt -Force
}
'UNINSTALL_EXIT=0'
