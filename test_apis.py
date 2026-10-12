import requests
import json
import xmltodict

VWORLD_KEY = "9FF03DCA-70F5-41A0-AC8B-0EB520A612B0"
MOLEG_OC = "usun7557"
ADDRESS = "서울시 성북구 길음동 1284"

def test_vworld_geocoder():
    print("--- 1. Testing VWorld Geocoder ---")
    url = "https://api.vworld.kr/req/address"
    params = {
        "service": "address",
        "request": "getcoord",
        "version": "2.0",
        "crs": "epsg:4326",
        "address": ADDRESS,
        "refine": "true",
        "simple": "false",
        "format": "json",
        "type": "PARCEL",
        "key": VWORLD_KEY
    }
    resp = requests.get(url, params=params)
    print("Geocoder status:", resp.status_code)
    try:
        data = resp.json()
        print(json.dumps(data, ensure_ascii=False, indent=2)[:1000])
        return data
    except Exception as e:
        print("Error:", e, resp.text[:500])
        return None

def test_vworld_search():
    print("\n--- 2. Testing VWorld Search ---")
    url = "https://api.vworld.kr/req/search"
    params = {
        "service": "search",
        "request": "search",
        "version": "2.0",
        "crs": "EPSG:4326",
        "size": "5",
        "page": "1",
        "query": ADDRESS,
        "type": "address",
        "category": "parcel",
        "format": "json",
        "key": VWORLD_KEY
    }
    resp = requests.get(url, params=params)
    print("Search status:", resp.status_code)
    try:
        data = resp.json()
        print(json.dumps(data, ensure_ascii=False, indent=2)[:1000])
        return data
    except Exception as e:
        print("Error:", e, resp.text[:500])
        return None

if __name__ == "__main__":
    test_vworld_geocoder()
    test_vworld_search()
