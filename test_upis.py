import requests
import json

VWORLD_KEY = "9FF03DCA-70F5-41A0-AC8B-0EB520A612B0"
X = "127.01794873996072"
Y = "37.60755731408648"

layers = [
    ("LT_C_UQ111", "용도지역 (도시지역)"),
    ("LT_C_UPISUQ151", "용도지구"),
    ("LT_C_UPISUQ161", "지구단위계획구역"),
    ("LT_C_UPISUQ171", "개발행위허가제한구역"),
    ("LT_C_UPISUQ174", "도시개발구역"),
    ("LT_C_UPISUQ175", "도시및주거환경정비구역 (재개발/재건축)"),
    ("LT_C_DGZONE", "정비구역 (대안)"),
]

url = "https://api.vworld.kr/req/data"

for layer_id, desc in layers:
    params = {
        "service": "data",
        "request": "GetFeature",
        "data": layer_id,
        "key": VWORLD_KEY,
        "geomFilter": f"POINT({X} {Y})",
        "geometry": "false",
        "crs": "EPSG:4326",
        "format": "json"
    }
    resp = requests.get(url, params=params)
    try:
        data = resp.json()
        status = data.get("response", {}).get("status")
        print(f"[{layer_id}] {desc}: {status}")
        if status == "OK":
            features = data.get("response", {}).get("result", {}).get("featureCollection", {}).get("features", [])
            for f in features:
                props = f.get("properties", {})
                print("  ->", json.dumps(props, ensure_ascii=False))
        elif status == "ERROR":
            print("  error:", data.get("response", {}).get("error"))
    except Exception as e:
        print("  parse error:", e)
