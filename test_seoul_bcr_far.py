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

url = f"https://www.law.go.kr/DRF/lawService.do?OC={OC}&target=ordin&MST=2149501&type=XML"
r = requests.get(url, headers=HEADERS)
d = xmltodict.parse(r.text)
articles = d['LawService']['조문']['조']

for a in articles:
    title = str(a.get('조제목', ''))
    content = str(a.get('조내용', ''))
    if "건폐율" in title or "용적률" in title:
        print(f"=== [{a.get('조문번호')}] {title} ===")
        print(content)
        # Check if there are 항/호
        print("-" * 50)
