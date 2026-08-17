#!/usr/bin/env python3
import argparse, datetime, hashlib, json, pathlib, re, struct

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest().upper()

def pe_sections(data):
    try:
        if data[:2] != b'MZ':
            return []
        peoff = struct.unpack_from('<I', data, 0x3C)[0]
        if data[peoff:peoff+4] != b'PE\0\0':
            return []
        machine, nsec, _tds, _ptrsym, _nsym, opt_size, _chars = struct.unpack_from('<HHIIIHH', data, peoff + 4)
        sec_off = peoff + 24 + opt_size
        rows = []
        for i in range(nsec):
            off = sec_off + i * 40
            name = data[off:off+8].split(b'\0', 1)[0].decode('latin1', 'replace')
            vsize, vaddr, raw_size, raw_ptr, _reloc, _line, _nrel, _nline, chars = struct.unpack_from('<IIIIIIHHI', data, off+8)
            rows.append({'name': name, 'virtual_size': vsize, 'virtual_address': vaddr, 'raw_size': raw_size, 'raw_ptr': raw_ptr, 'characteristics': hex(chars)})
        return rows
    except Exception as e:
        return [{'parse_error': repr(e)}]

def collect_strings(data, enc='ascii', min_len=4, limit=20000):
    if enc == 'utf16le':
        pat = rb'(?:[\x20-\x7e]\x00){%d,}' % min_len
        out = []
        for m in re.finditer(pat, data):
            try: s = m.group().decode('utf-16le', 'replace')
            except Exception: continue
            out.append({'off': m.start(), 's': s[:500], 'enc': enc})
            if len(out) >= limit: break
        return out
    pat = rb'[\x20-\x7e]{%d,}' % min_len
    out = []
    for m in re.finditer(pat, data):
        out.append({'off': m.start(), 's': m.group().decode('latin1', 'replace')[:500], 'enc': 'ascii'})
        if len(out) >= limit: break
    return out

def main():
    ap = argparse.ArgumentParser(description='PE/string/IP/URL surface scanner for offline black-box triage.')
    ap.add_argument('file')
    ap.add_argument('--out', default=None)
    ap.add_argument('--keyword', action='append', default=[])
    ap.add_argument('--limit', type=int, default=500)
    args = ap.parse_args()
    path = pathlib.Path(args.file).expanduser().resolve()
    data = path.read_bytes()
    strings = collect_strings(data, 'ascii') + collect_strings(data, 'utf16le')
    default_keywords = ['http','https','tcp','udp','socket','card','key','lic','license','login','auth','token','vip','admin','expire','update','server','proxy','SimpleCard','卡密','登录','试用','永久','权限','错误','成功']
    keywords = [k.lower() for k in (default_keywords + args.keyword)]
    hits = []
    for row in strings:
        low = row['s'].lower()
        if any(k in low for k in keywords):
            hits.append(row)
            if len(hits) >= args.limit: break
    ips = sorted(set(x.decode('latin1','replace') for x in re.findall(rb'(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)', data)))
    urls = sorted(set(x.decode('latin1','replace') for x in re.findall(rb'https?://[^\s\x00"\'<>]{4,240}', data)))
    cn_hits = []
    for term in ['卡密','登录','成功','错误','试用','永久','权限','网络','服务器','机器码']:
        for enc in ('gbk','utf-8','utf-16le'):
            pat = term.encode(enc, 'ignore')
            start = 0
            while pat:
                i = data.find(pat, start)
                if i < 0: break
                cn_hits.append({'term': term, 'enc': enc, 'off': i})
                start = i + 1
                if len(cn_hits) >= args.limit: break
            if len(cn_hits) >= args.limit: break
        if len(cn_hits) >= args.limit: break
    result = {'file': str(path), 'size': path.stat().st_size, 'sha256': sha256_file(path), 'sections': pe_sections(data), 'ips': ips[:300], 'urls': urls[:300], 'string_hits': hits, 'cn_hits': cn_hits, 'generated': datetime.datetime.now().isoformat()}
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        pathlib.Path(args.out).write_text(text, encoding='utf-8')
    print(text)
if __name__ == '__main__':
    main()
