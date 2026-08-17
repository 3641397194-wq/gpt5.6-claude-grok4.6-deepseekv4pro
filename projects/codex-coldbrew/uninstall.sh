#!/bin/sh
set -eu

name='eni-coldbrew'
root="${1:-$HOME/.codex/skills}"
target="$root/$name"
receipt="$root/.$name.receipt"
test -f "$receipt" || { echo "Receipt not found: $receipt" >&2; exit 2; }
recorded_target=$(sed -n 's/^target=//p' "$receipt")
backup=$(sed -n 's/^backup=//p' "$receipt")
previous_receipt_file=$(sed -n 's/^previous_receipt_file=//p' "$receipt")
test "$recorded_target" = "$target" || { echo 'Receipt target mismatch' >&2; exit 3; }
case "$backup" in
  '') ;;
  "$target".backup-*) test -e "$backup" || { echo "Backup missing: $backup" >&2; exit 4; } ;;
  *) echo "Unsafe backup path: $backup" >&2; exit 5 ;;
esac
case "$previous_receipt_file" in
  '') ;;
  "$target".backup-*.receipt) test -f "$previous_receipt_file" || { echo "Previous receipt missing: $previous_receipt_file" >&2; exit 6; } ;;
  *) echo "Unsafe previous receipt path: $previous_receipt_file" >&2; exit 7 ;;
esac
test -z "$previous_receipt_file" || test -n "$backup" || { echo 'Previous receipt without backup' >&2; exit 8; }
rm -rf "$target"
if test -n "$backup" && test -e "$backup"; then
  mv "$backup" "$target"
  printf 'RESTORED_BACKUP=%s\n' "$target"
fi
if test -n "$previous_receipt_file" && test -f "$previous_receipt_file"; then
  mv "$previous_receipt_file" "$receipt"
  echo 'RESTORED_PREVIOUS_RECEIPT=1'
else
  rm -f "$receipt"
fi
echo 'UNINSTALL_EXIT=0'
