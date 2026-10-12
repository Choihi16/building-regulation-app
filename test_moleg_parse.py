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

def search_and_get_detail(query, target_org=None):
    url = f"https://www.law.go.kr/DRF/lawSearch.do?OC={OC}&target=ordin&type=XML&query={requests.utils.quote(query)}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    data = xmltodict.parse(resp.content.decode('utf-8'))
    root = data.get('OrdinSearch', {})
    laws = root.get('law', [])
    if isinstance(laws, dict):
        laws = [laws]
    
    print(f"\n==================================================")
    print(f"Query: {query} (Found {len(laws)} items)")
    matched = None
    for l in laws:
        title = l.get('자치법규명', '')
        org = l.get('지자체기관명', '')
        print(f"- {title} | {org} | MST={l.get('자치법규일련번호')} | ID={l.get('자치법규ID')}")
        if target_org:
            if target_org in org and (query in title or "조례" in title):
                matched = l
                break
        else:
            if not matched:
                matched = l
    
    if not matched and laws:
        matched = laws[0]
        
    if matched:
        mst = matched.get('자치법규일련번호')
        title = matched.get('자치법규명')
        org = matched.get('지자체기관명')
        print(f"\n>>> Selected: {title} ({org}), fetching lawService MST={mst}...")
        detail_url = f"https://www.law.go.kr/DRF/lawService.do?OC={OC}&target=ordin&MST={mst}&type=XML"
        det_resp = requests.get(detail_url, headers=HEADERS, timeout=10)
        det_data = xmltodict.parse(det_resp.content.decode('utf-8'))
        det_root = det_data.get('자치법규', {}) or det_data.get('OrdinService', {})
        print("Detail root tag:", list(det_data.keys()))
        if '자치법규' in det_data:
            binfo = det_data['자치법규'].get('기본정보', {})
            print(f"기본정보: {binfo.get('자치법규명')}, 소관기관: {binfo.get('소관부서명') or binfo.get('지자체기관명')}")
            articles = det_data['자치법규'].get('조문', {}).get('조문단위', [])
            if isinstance(articles, dict):
                articles = [articles]
            print(f"Total articles: {len(articles)}")
            for a in articles:
                atitle = str(a.get('조문제목', ''))
                acontent = str(a.get('조문내용', ''))
                if any(k in atitle for k in ["건폐율", "용적률", "높이", "심의", "위원회"]):
                    print(f"  * {atitle}: {acontent[:100]}...")

if __name__ == "__main__":
    search_and_get_detail("서울특별시 도시계획 조례", "서울특별시")
    search_and_get_detail("서울특별시 건축 조례", "서울특별시")
    search_and_get_detail("성북구 건축 조례", "성북구")
