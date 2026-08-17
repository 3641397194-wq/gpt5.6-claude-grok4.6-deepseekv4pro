#!/bin/sh
set -eu

name='eni-coldbrew'
root="${1:-$HOME/.codex/skills}"
replace="${2:-}"
base="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
source_dir="$base/skills/eni-coldbrew"
version=$(tr -d '\r\n' < "$base/VERSION")
printf '%s\n' "$version" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' || { echo 'Invalid VERSION' >&2; exit 2; }
target="$root/$name"
receipt="$root/.$name.receipt"
operation_stamp=$(date +%Y%m%d-%H%M%S)
operation_counter=0
while :; do
  operation_id="$operation_stamp-$$-$operation_counter"
  receipt_tmp="$receipt.tmp-$operation_id"
  stage="$root/.$name.stage-$operation_id"
  test -e "$receipt_tmp" || test -e "$stage" || break
  operation_counter=$((operation_counter + 1))
done
backup=''
previous_receipt_file=''
moved_old=0
installed_new=0

cleanup() {
  code=$?
  trap - EXIT HUP INT TERM
  rm -rf "$stage"
  rm -f "$receipt_tmp"
  if test "$code" -ne 0 && test "$installed_new" -eq 1; then rm -rf "$target"; fi
  if test "$code" -ne 0 && test "$moved_old" -eq 1 && test -e "$backup"; then
    mv "$backup" "$target"
  fi
  if test "$code" -ne 0; then test -z "$previous_receipt_file" || rm -f "$previous_receipt_file"; fi
  exit "$code"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

test -f "$source_dir/SKILL.md" || { echo 'Missing source Skill' >&2; exit 2; }
mkdir -p "$root"
if test -e "$receipt"; then
  test "$replace" = '--replace' || { echo "Existing receipt: $receipt; pass --replace to upgrade" >&2; exit 3; }
  recorded_target=$(sed -n 's/^target=//p' "$receipt")
  test "$recorded_target" = "$target" || { echo 'Existing receipt target mismatch' >&2; exit 5; }
  test -e "$target" || { echo "Receipt exists but installed Skill is missing: $target" >&2; exit 6; }
fi
if test -e "$target"; then
  test "$replace" = '--replace' || { echo 'Skill exists; pass --replace' >&2; exit 4; }
  counter=0
  while :; do
    backup="$target.backup-$(date +%Y%m%d-%H%M%S)-$$-$counter"
    test -e "$backup" || test -e "$backup.receipt" || break
    counter=$((counter + 1))
  done
  if test -e "$receipt"; then
    previous_receipt_file="$backup.receipt"
    cp "$receipt" "$previous_receipt_file"
  fi
  mv "$target" "$backup"
  moved_old=1
fi

cp -R "$source_dir" "$stage"
mv "$stage" "$target"
installed_new=1
printf 'schema=3\nname=%s\ntarget=%s\nbackup=%s\nprevious_receipt_file=%s\nversion=%s\n' \
  "$name" "$target" "$backup" "$previous_receipt_file" "$version" > "$receipt_tmp"
mv "$receipt_tmp" "$receipt"
trap - EXIT HUP INT TERM
printf 'INSTALL_TARGET=%s\nINSTALL_BACKUP=%s\nINSTALL_EXIT=0\n' "$target" "$backup"
