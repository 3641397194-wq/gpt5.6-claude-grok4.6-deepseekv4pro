#!/usr/bin/env python3
import argparse, datetime, hashlib, json, pathlib, shutil, sys

def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest().upper()

def inventory(root: pathlib.Path, limit=20000):
    rows = []
    if root.is_file():
        return [{'path': str(root), 'rel': root.name, 'size': root.stat().st_size, 'sha256': sha256_file(root)}]
    for p in root.rglob('*'):
        if len(rows) >= limit:
            break
        if p.is_file():
            rows.append({'path': str(p), 'rel': str(p.relative_to(root)), 'size': p.stat().st_size, 'sha256': sha256_file(p)})
    return rows

def main():
    ap = argparse.ArgumentParser(description='Create an add-only offline black-box case workspace and copy/hash a target.')
    ap.add_argument('target', help='Target file or folder')
    ap.add_argument('--cases-root', default=str(pathlib.Path.cwd() / 'cases'), help='Root directory for cases')
    ap.add_argument('--name', default='offline-blackbox', help='Case name prefix')
    ap.add_argument('--out-json', default=None, help='Optional output JSON path')
    args = ap.parse_args()
    target = pathlib.Path(args.target).expanduser().resolve()
    if not target.exists():
        raise SystemExit(f'target not found: {target}')
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    case = pathlib.Path(args.cases_root).expanduser().resolve() / f'{args.name}-{ts}'
    artifacts = case / 'artifacts'; triage = case / 'triage'; reports = case / 'reports'; scripts = case / 'scripts'
    for d in (artifacts, triage, reports, scripts):
        d.mkdir(parents=True, exist_ok=True)
    dest = artifacts / target.name
    if target.is_dir():
        shutil.copytree(target, dest)
    else:
        shutil.copy2(target, dest)
    data = {'case': str(case), 'original': str(target), 'artifact_copy': str(dest), 'created': ts, 'inventory': inventory(dest)}
    out = pathlib.Path(args.out_json).expanduser().resolve() if args.out_json else triage / 'case_inventory.json'
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'case': str(case), 'artifact_copy': str(dest), 'out_json': str(out), 'file_count': len(data['inventory'])}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
