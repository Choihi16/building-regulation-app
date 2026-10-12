import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
import xmltodict

OC = "usun7557"
HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.law.go.kr"}

# Search 서울특별시 건축 조례
url = f"https://www.law.go.kr/DRF/lawSearch.do?OC={OC}&target=ordin&type=XML&query={requests.utils.quote('서울특별시 건축 조례')}"
r = requests.get(url, headers=HEADERS)
d = xmltodict.parse(r.text)
laws = d.get('OrdinSearch', {}).get('law', [])
if isinstance(laws, dict): laws = [laws]

seoul_bld = None
for l in laws:
    if l.get('자치법규명') == '서울특별시 건축 조례':
        seoul_bld = l
        break

if seoul_bld:
    mst = seoul_bld.get('자치법규일련번호')
    print(f"Found 서울특별시 건축 조례: MST={mst}")
    url2 = f"https://www.law.go.kr/DRF/lawService.do?OC={OC}&target=ordin&MST={mst}&type=XML"
    r2 = requests.get(url2, headers=HEADERS)
    d2 = xmltodict.parse(r2.text)
    articles = d2['LawService']['조문']['조']
    for a in articles:
        title = str(a.get('조제목', ''))
        content = str(a.get('조내용', ''))
        if any(k in title for k in ["심의", "높이", "일조", "가로구역"]):
            print(f"=== {a.get('조문번호')} {title} ===")
            print(content[:350])
            print("-" * 50)
