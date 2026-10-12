import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
import xmltodict
import json

OC = "usun7557"

def search_ordinance(query):
    url = "https://www.law.go.kr/DRF/lawSearch.do"
    params = {
        "OC": OC,
        "target": "ordin",
        "type": "XML",
        "query": query,
        "display": 10
    }
    resp = requests.get(url, params=params, verify=False)
    print(f"\n=== Query: {query} (Status {resp.status_code}) ===")
    try:
        data = xmltodict.parse(resp.content.decode('utf-8'))
        # print keys
        root = data.get('OrdinSearch') or data.get('ordin') or data.get('LawSearch')
        if root:
            total = root.get('totalCnt', 'unknown')
            print(f"Total count: {total}")
            items = root.get('ordin', [])
            if isinstance(items, dict):
                items = [items]
            for it in items[:5]:
                print(f"- [{it.get('자치법규ID') or it.get('자치법규일련번호')}] {it.get('자치법규명')} ({it.get('지자체기관명')}) - 공포일자: {it.get('공포일자')}")
                print(f"  상세링크: {it.get('자치법규상세링크')}")
            return items
        else:
            print("Unknown structure:", list(data.keys()))
            print(str(data)[:500])
    except Exception as e:
        print("Error parsing XML:", e)
        print(resp.text[:500])

if __name__ == "__main__":
    search_ordinance("서울특별시 도시계획 조례")
    search_ordinance("서울특별시 성북구 도시계획 조례")
    search_ordinance("서울특별시 성북구 건축 조례")
    search_ordinance("성북구 건축 조례")
