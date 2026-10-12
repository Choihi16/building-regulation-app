import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
import xmltodict
import json

OC = "usun7557"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.law.go.kr"
}

def search_ordinance(query):
    url = f"https://www.law.go.kr/DRF/lawSearch.do?OC={OC}&target=ordin&type=XML&query={requests.utils.quote(query)}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    print(f"\n--- Searching: {query} (status: {resp.status_code}) ---")
    data = xmltodict.parse(resp.content.decode('utf-8'))
    root = data.get('OrdinSearch', {})
    total = root.get('totalCnt', 0)
    print(f"Total: {total}")
    items = root.get('ordin', [])
    if isinstance(items, dict):
        items = [items]
    for it in items[:3]:
        print(f"Title: {it.get('자치법규명')}")
        print(f"Org: {it.get('지자체기관명')}")
        print(f"Seq: {it.get('자치법규일련번호')}")
        print(f"ID: {it.get('자치법규ID')}")
        print(f"Detail Link: {it.get('자치법규상세링크')}")
    if items:
        return items[0].get('자치법규일련번호'), items[0].get('자치법규ID')
    return None, None

def get_ordinance_detail(seq, ordin_id):
    print(f"\n--- Fetching detail for seq={seq}, id={ordin_id} ---")
    # DRF detail API: target=ordin, MST={seq} or ID={ordin_id}
    url1 = f"https://www.law.go.kr/DRF/lawService.do?OC={OC}&target=ordin&MST={seq}&type=XML"
    resp = requests.get(url1, headers=HEADERS, timeout=10)
    print("lawService MST status:", resp.status_code)
    try:
        data = xmltodict.parse(resp.content.decode('utf-8'))
        root = data.get('OrdinService', {})
        print("OrdinService keys:", list(root.keys()))
        bld = root.get('기본정보', {})
        print("기본정보:", bld.get('자치법규명'), bld.get('지자체기관명'), bld.get('시행일자'))
        articles = root.get('조문', {}).get('조문단위', [])
        if isinstance(articles, dict):
            articles = [articles]
        print(f"조문 개수: {len(articles)}")
        # Look for 건폐율, 용적률, 높이, 심의 관련 조문
        keywords = ["건폐율", "용적률", "높이", "심의", "위원회"]
        matched = []
        for a in articles:
            title = str(a.get('조문제목', ''))
            content = str(a.get('조문내용', ''))
            for k in keywords:
                if k in title or k in content:
                    matched.append((a.get('조문번호'), title, content[:150]))
                    break
        print(f"키워드 매칭된 조문 수: {len(matched)}")
        for num, t, c in matched[:5]:
            print(f"  [제{num}조 {t}]: {c}...")
    except Exception as e:
        print("Error parsing detail:", e)
        print(resp.text[:500])

if __name__ == "__main__":
    seq, oid = search_ordinance("서울특별시 도시계획 조례")
    if seq:
        get_ordinance_detail(seq, oid)
