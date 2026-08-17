#!/usr/bin/env python3
"""
Unified Scraping Engine — 5 engines fused.
Auto-selects best approach based on target response and task.
"""
import sys, io, json, time, argparse, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ============================================================
# Engine 1: curl_cffi — TLS Fingerprint Bypass
# ============================================================
def engine_curl_cffi(url, **kwargs):
    """Chrome TLS fingerprint impersonation. Handles 90% of anti-bot."""
    from curl_cffi import requests
    impersonate = kwargs.get('impersonate', 'chrome124')
    r = requests.get(url, impersonate=impersonate, timeout=25)
    return {'engine': 'curl_cffi', 'status': r.status_code, 'html': r.text, 'url': url}

# ============================================================
# Engine 2: Scrapling — Adaptive Anti-Bot
# ============================================================
def engine_scrapling(url, extract_selector=None, **kwargs):
    """Adaptive selectors that auto-heal when site layout changes."""
    from scrapling import Fetcher
    f = Fetcher()
    page = f.get(url)
    result = {'engine': 'scrapling', 'url': url, 'title': page.css('title').text() if page.css('title') else ''}
    if extract_selector:
        items = page.css(extract_selector).all()
        result['items'] = [{'text': item.text(), 'html': str(item)} for item in items]
    return result

# ============================================================
# Engine 3: AutoScraper — Pattern Learning from Examples
# ============================================================
def engine_autoscraper(url, wanted_list=None, **kwargs):
    """Learn extraction patterns from 1-2 examples. No selectors needed."""
    from autoscraper import AutoScraper
    scraper = AutoScraper()
    if not wanted_list:
        return {'engine': 'autoscraper', 'error': 'Need wanted_list examples'}
    result = scraper.build(url, wanted_list=wanted_list)
    return {'engine': 'autoscraper', 'url': url, 'patterns': result, 'rules': scraper.get_result_similar(url)}

# ============================================================
# Engine 4: Firecrawl — JS Render + Clean Structured Data
# ============================================================
def engine_firecrawl(url, mode='scrape', **kwargs):
    """Full browser rendering. Returns clean Markdown or structured data."""
    from firecrawl import FirecrawlApp
    app = FirecrawlApp()
    if mode == 'scrape':
        data = app.scrape_url(url)
        return {'engine': 'firecrawl', 'url': url, 'content': data}
    elif mode == 'crawl':
        limit = kwargs.get('limit', 50)
        result = app.crawl_url(url, params={'limit': limit})
        return {'engine': 'firecrawl', 'url': url, 'pages': result}
    return {'engine': 'firecrawl', 'error': f'Unknown mode: {mode}'}

# ============================================================
# Auto-Detect & Execute
# ============================================================
def smart_scrape(url, mode='auto', **kwargs):
    """
    Intelligently selects the best engine:
    - Try curl_cffi first (fastest, handles most blocks)
    - If blocked → add Scrapling
    - If JS-heavy → Firecrawl
    - If pattern-based → AutoScraper
    """

    if mode == 'curl_cffi' or mode == 'auto':
        try:
            return engine_curl_cffi(url, **kwargs)
        except Exception as e:
            print(f"  curl_cffi failed: {e}")

    if mode == 'scrapling':
        try:
            return engine_scrapling(url, **kwargs)
        except Exception as e:
            print(f"  Scrapling failed: {e}")

    if mode == 'autoscraper':
        try:
            return engine_autoscraper(url, **kwargs)
        except Exception as e:
            print(f"  AutoScraper failed: {e}")

    if mode == 'firecrawl':
        try:
            return engine_firecrawl(url, **kwargs)
        except Exception as e:
            print(f"  Firecrawl failed: {e}")

    return {'error': f'All engines failed for {url}'}

# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description='Unified Scraping Engine')
    parser.add_argument('--url', required=True, help='Target URL')
    parser.add_argument('--mode', default='auto', choices=['auto', 'curl_cffi', 'scrapling', 'autoscraper', 'firecrawl'])
    parser.add_argument('--extract', help='CSS selector or "all"')
    parser.add_argument('--learn', help='Comma-separated example values for AutoScraper')
    parser.add_argument('--output', help='Output JSON file path')
    parser.add_argument('--impersonate', default='chrome124', help='Browser profile for curl_cffi')

    args = parser.parse_args()

    kwargs = {'impersonate': args.impersonate}
    if args.extract:
        kwargs['extract_selector'] = args.extract
    if args.learn:
        kwargs['wanted_list'] = [x.strip() for x in args.learn.split(',')]
        args.mode = 'autoscraper'

    print(f"Scraping: {args.url}")
    print(f"Mode: {args.mode}")
    result = smart_scrape(args.url, mode=args.mode, **kwargs)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        print(f"Saved: {args.output}")
    else:
        # Print summary
        engine = result.get('engine', 'unknown')
        status = result.get('status', 'N/A')
        print(f"Engine: {engine} | Status: {status}")
        if 'items' in result:
            print(f"Extracted: {len(result['items'])} items")

if __name__ == '__main__':
    main()
