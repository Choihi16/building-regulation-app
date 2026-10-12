import sys
sys.stdout.reconfigure(encoding='utf-8')
import re
from moleg_api import MolegClient

moleg = MolegClient()
bundle = moleg.get_municipal_ordinance_bundle("서울특별시", "성북구")
far_articles = bundle.get("far_articles", [])

print(f"Total FAR articles: {len(far_articles)}")
for a in far_articles:
    title = a.get("title", "")
    content = a.get("content", "")
    lines = content.split("\n")
    for line in lines:
        if "제3종일반주거지역" in line and "퍼센트" in line:
            print(f"[{a.get('num')} - {title}] Matched line:")
            print("  ", line.strip())
