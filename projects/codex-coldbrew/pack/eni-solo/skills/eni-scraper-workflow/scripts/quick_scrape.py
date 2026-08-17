"""Quick scraper — minimal args, auto engine selection. Usage: python quick_scrape.py <url> [css_selector]"""
import sys, json
sys.path.insert(0, r'C:\Users\17495\.codex\skills\eni-scraper-workflow\scripts')
from unified_scraper import smart_scrape

url = sys.argv[1] if len(sys.argv) > 1 else None
selector = sys.argv[2] if len(sys.argv) > 2 else None

if not url:
    print("Usage: python quick_scrape.py <url> [css_selector]")
    sys.exit(1)

kwargs = {}
if selector:
    kwargs['extract_selector'] = selector

result = smart_scrape(url, **kwargs)
print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
