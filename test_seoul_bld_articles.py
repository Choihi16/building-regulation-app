import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
import xmltodict

OC = "usun7557"
HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.law.go.kr"}

url = f"https://www.law.go.kr/DRF/lawService.do?OC={OC}&target=ordin&MST=2116749&type=XML"
r = requests.get(url, headers=HEADERS)
d = xmltodict.parse(r.text)
articles = d['LawService']['조문']['조']

for a in articles:
    title = str(a.get('조제목', ''))
    content = str(a.get('조내용', ''))
    if any(k in title for k in ["심의", "높이", "일조", "가로구역", "위원회"]):
        print(f"=== {a.get('조문번호')} {title} ===")
        print(content[:400])
        print("-" * 50)
