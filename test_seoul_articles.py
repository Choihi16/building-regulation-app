import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
import xmltodict
import json

OC = "usun7557"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.law.go.kr"
}

def find_exact_ordinance(query, target_org=None):
    url = f"https://www.law.go.kr/DRF/lawSearch.do?OC={OC}&target=ordin&type=XML&query={requests.utils.quote(query)}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    data = xmltodict.parse(resp.content.decode('utf-8'))
    laws = data.get('OrdinSearch', {}).get('law', [])
    if isinstance(laws, dict):
        laws = [laws]
    
    print(f"Results for '{query}':")
    matched = None
    for l in laws:
        title = l.get('자치법규명', '')
        org = l.get('지자체기관명', '')
        print(f"  [{l.get('자치법규일련번호')}] {title} | {org}")
        if target_org and org == target_org:
            if not matched:
                matched = l
        elif not target_org and not matched:
            matched = l
    return matched

if __name__ == "__main__":
    # 1. Seoul Urban Planning Ordinance
    l1 = find_exact_ordinance("서울특별시 도시계획 조례", "서울특별시")
    if l1:
        mst = l1.get('자치법규일련번호')
        url = f"https://www.law.go.kr/DRF/lawService.do?OC={OC}&target=ordin&MST={mst}&type=XML"
        r = requests.get(url, headers=HEADERS)
        d = xmltodict.parse(r.text)
        articles = d.get('LawService', {}).get('조문', {}).get('조', [])
        print(f"\n--- Found {len(articles)} articles in {l1.get('자치법규명')} ---")
        for a in articles:
            t = str(a.get('조제목', ''))
            c = str(a.get('조내용', ''))
            if "건폐율" in t or "용적률" in t or "높이" in t:
                print(f"\n[{a.get('조문번호')} - {t}]\n{c[:300]}...")
