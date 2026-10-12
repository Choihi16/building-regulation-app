import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
import json

VWORLD_KEY = "9FF03DCA-70F5-41A0-AC8B-0EB520A612B0"
X = "127.01794873996072"
Y = "37.60755731408648"

test_layers = [
    # 용도지역
    "LT_C_UQ111", # 도시지역 (주거, 상업, 공업, 녹지)
    "LT_C_UQ112", # 관리지역
    "LT_C_UQ113", # 농림지역
    "LT_C_UQ114", # 자연환경보전지역
    # 용도지구
    "LT_C_UQ121", # 경관지구
    "LT_C_UQ122", # 고도지구
    "LT_C_UQ123", # 방화지구
    "LT_C_UQ124", # 방재지구
    "LT_C_UQ125", # 보호지구
    "LT_C_UQ126", # 취락지구
    "LT_C_UQ127", # 개발진흥지구
    "LT_C_UQ128", # 특정용도제한지구
    "LT_C_UQ129", # 복합용도지구
    # 용도구역 / 지구단위계획
    "LT_C_UQ130", # 지구단위계획구역
    "LT_C_UQ141", # 입지규제최소구역
    "LT_C_UPISUQ161", # 지구단위계획구역 (UPIS)
    "LT_C_UPISUQ151", # 용도지구
    "LT_C_UPISUQ171", # 개발행위허가제한구역
    "LT_C_UPISUQ174", # 도시개발구역
    "LT_C_UPISUQ175", # 정비구역
    "LT_C_G101", # 연속지적도
    "LT_C_LANDINFO", # 토지이용계획
    "LT_L_FRSTCL", # 산림
]

url = "https://api.vworld.kr/req/data"

for layer in test_layers:
    params = {
        "service": "data",
        "request": "GetFeature",
        "data": layer,
        "key": VWORLD_KEY,
        "domain": "localhost",
        "geomFilter": f"POINT({X} {Y})",
        "geometry": "false",
        "crs": "EPSG:4326",
        "format": "json"
    }
    resp = requests.get(url, params=params)
    data = resp.json()
    status = data.get("response", {}).get("status")
    if status == "OK":
        items = data.get("response", {}).get("result", {}).get("featureCollection", {}).get("features", [])
        names = [f.get("properties", {}).get("uname") or f.get("properties", {}).get("name") or str(f.get("properties")) for f in items]
        print(f"[{layer}] OK: {names}")
    elif status == "NOT_FOUND":
        print(f"[{layer}] Valid layer, but NOT_FOUND at this point")
    else:
        err = data.get("response", {}).get("error", {})
        print(f"[{layer}] {status}: {err.get('code')} - {err.get('text')}")
