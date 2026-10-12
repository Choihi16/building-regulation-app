import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
import json
import xmltodict

VWORLD_KEY = "9FF03DCA-70F5-41A0-AC8B-0EB520A612B0"
OC = "usun7557"
HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.law.go.kr"}

sample_addresses = [
    "서울시 성북구 길음동 1284",
    "경기도 성남시 분당구 정자동 178-1",
    "부산광역시 해운대구 우동 1408"
]

def analyze_sample(addr):
    print(f"\n=======================================================")
    print(f"Testing Address: {addr}")
    
    # 1. Geocoder
    g_url = "https://api.vworld.kr/req/address"
    g_params = {
        "service": "address",
        "request": "getcoord",
        "version": "2.0",
        "crs": "epsg:4326",
        "address": addr,
        "refine": "true",
        "simple": "false",
        "format": "json",
        "type": "PARCEL",
        "key": VWORLD_KEY
    }
    g_resp = requests.get(g_url, params=g_params).json()
    status = g_resp.get("response", {}).get("status")
    if status != "OK":
        g_params["type"] = "ROAD"
        g_resp = requests.get(g_url, params=g_params).json()
    
    refined = g_resp.get("response", {}).get("refined", {})
    point = g_resp.get("response", {}).get("result", {}).get("point", {})
    x = point.get("x")
    y = point.get("y")
    structure = refined.get("structure", {})
    pnu = structure.get("level4LC")
    level1 = structure.get("level1")
    level2 = structure.get("level2")
    
    print(f"Refined: {refined.get('text')}")
    print(f"PNU: {pnu}, Coord: ({x}, {y})")
    print(f"Admin: {level1} / {level2}")
    
    # 2. Zoning from V-World Data API
    zoning_list = []
    is_district_plan = False
    
    # Check LT_C_UQ111
    d_url = "https://api.vworld.kr/req/data"
    d_params = {
        "service": "data",
        "request": "GetFeature",
        "data": "LT_C_UQ111",
        "key": VWORLD_KEY,
        "domain": "localhost",
        "geomFilter": f"POINT({x} {y})",
        "geometry": "false",
        "crs": "EPSG:4326",
        "format": "json"
    }
    d_resp = requests.get(d_url, params=d_params).json()
    if d_resp.get("response", {}).get("status") == "OK":
        features = d_resp.get("response", {}).get("result", {}).get("featureCollection", {}).get("features", [])
        for f in features:
            uname = f.get("properties", {}).get("uname")
            if uname and uname not in zoning_list:
                zoning_list.append(uname)
                
    # Check LT_C_UPISUQ161 (지구단위계획)
    d_params["data"] = "LT_C_UPISUQ161"
    d_resp = requests.get(d_url, params=d_params).json()
    district_plan_names = []
    if d_resp.get("response", {}).get("status") == "OK":
        is_district_plan = True
        features = d_resp.get("response", {}).get("result", {}).get("featureCollection", {}).get("features", [])
        for f in features:
            name = f.get("properties", {}).get("uname") or f.get("properties", {}).get("name")
            if name: district_plan_names.append(name)
            
    print(f"Zonings: {zoning_list}")
    print(f"District Plan Area: {is_district_plan} ({district_plan_names})")
    
    # 3. MOLEG Ordinance search
    # Find Urban Planning Ordinance
    search_q = f"{level1} 도시계획 조례" if "특별시" in level1 or "광역시" in level1 or "특별자치" in level1 else f"{level2.split()[0]} 도시계획 조례"
    s_url = f"https://www.law.go.kr/DRF/lawSearch.do?OC={OC}&target=ordin&type=XML&display=20&query={requests.utils.quote(search_q)}"
    s_resp = requests.get(s_url, headers=HEADERS)
    s_data = xmltodict.parse(s_resp.content.decode('utf-8'))
    laws = s_data.get('OrdinSearch', {}).get('law', [])
    if isinstance(laws, dict): laws = [laws]
    print(f"Found {len(laws)} ordinances for '{search_q}'")
    for l in laws[:2]:
        print(f"  * {l.get('자치법규명')} ({l.get('지자체기관명')})")

if __name__ == "__main__":
    for a in sample_addresses:
        analyze_sample(a)
