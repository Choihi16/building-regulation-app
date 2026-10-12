import requests
import json

VWORLD_KEY = "9FF03DCA-70F5-41A0-AC8B-0EB520A612B0"
PNU = "1129013400112840000"
X = "127.01794873996072"
Y = "37.60755731408648"

def test_vworld_data_layers():
    # Test LT_C_UQ111 (용도지역) using POINT geomFilter and attrFilter
    url = "https://api.vworld.kr/req/data"
    
    layers = [
        ("LT_C_UQ111", "용도지역 (도시지역)"),
        ("LT_C_UQ112", "용도지역 (관리지역)"),
        ("LT_C_UQ113", "용도지역 (농림지역)"),
        ("LT_C_UQ114", "용도지역 (자연환경보전지역)"),
        ("LT_C_UQ115", "지구단위계획구역"),
        ("LT_C_UQ121", "도시및주거환경정비구역 (재개발/재건축)"),
        ("LT_C_UQ122", "재정비촉진지구"),
        ("LT_C_UQ129", "토지거래계약허가구역"),
    ]
    
    for layer_id, desc in layers:
        print(f"\n--- Checking {layer_id} ({desc}) ---")
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
        print("Status:", resp.status_code)
        try:
            data = resp.json()
            status = data.get("response", {}).get("status")
            print("Status in JSON:", status)
            if status == "OK":
                features = data.get("response", {}).get("result", {}).get("featureCollection", {}).get("features", [])
                for f in features:
                    props = f.get("properties", {})
                    print("Properties:", json.dumps(props, ensure_ascii=False))
            else:
                print("Result not OK:", data.get("response", {}).get("error", "No error msg"))
        except Exception as e:
            print("Parse error:", e, resp.text[:200])

if __name__ == "__main__":
    test_vworld_data_layers()
