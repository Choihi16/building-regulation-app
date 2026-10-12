import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests

OC = "usun7557"

def test_law_endpoints():
    test_urls = [
        "http://www.law.go.kr/DRF/lawSearch.do?OC=usun7557&target=ordin&type=XML&query=서울특별시+도시계획조례",
        "https://www.law.go.kr/DRF/lawSearch.do?OC=usun7557&target=ordin&type=XML&query=서울특별시+도시계획조례",
        "http://www.law.go.kr/DRF/lawSearch.do?OC=usun7557&target=ordin&type=HTML&query=서울특별시+도시계획조례",
        "http://apis.data.go.kr/... ",
    ]
    
    headers_list = [
        {},
        {"User-Agent": "Mozilla/5.0", "Referer": "http://localhost"},
        {"User-Agent": "Mozilla/5.0", "Referer": "http://127.0.0.1"},
        {"User-Agent": "Mozilla/5.0", "Referer": "https://www.law.go.kr"},
    ]
    
    for headers in headers_list:
        print("Headers:", headers)
        r = requests.get(test_urls[0], headers=headers)
        print("Resp:", r.text[:200])

if __name__ == "__main__":
    test_law_endpoints()
