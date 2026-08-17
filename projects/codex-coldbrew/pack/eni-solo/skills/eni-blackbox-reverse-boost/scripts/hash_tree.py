#!/usr/bin/env python3
import argparse, hashlib, json, pathlib

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest().upper()

def main():
    ap = argparse.ArgumentParser(description='Recursive SHA256 inventory for a file or folder.')
    ap.add_argument('path')
    ap.add_argument('--out', default=None)
    ap.add_argument('--limit', type=int, default=50000)
    args = ap.parse_args()
    root = pathlib.Path(args.path).expanduser().resolve()
    rows = []
    if root.is_file():
        rows.append({'path': str(root), 'rel': root.name, 'size': root.stat().st_size, 'sha256': sha256_file(root)})
    else:
        for p in root.rglob('*'):
            if len(rows) >= args.limit:
                break
            if p.is_file():
                rows.append({'path': str(p), 'rel': str(p.relative_to(root)), 'size': p.stat().st_size, 'sha256': sha256_file(p)})
    data = {'root': str(root), 'count': len(rows), 'files': rows}
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if args.out:
        pathlib.Path(args.out).write_text(text, encoding='utf-8')
    print(text)
if __name__ == '__main__':
    main()
