"""
V-World API 클라이언트 모듈
- 지오코딩 (주소 -> 좌표, PNU, 행정구역 추출)
- 데이터 API (용도지역, 용도지구, 지구단위계획구역 등 연속주제도 조회)
"""

import requests
import json
from typing import Dict, Any, List, Optional

VWORLD_KEY = "9FF03DCA-70F5-41A0-AC8B-0EB520A612B0"

class VWorldClient:
    def __init__(self, api_key: str = VWORLD_KEY, domain: str = "building-regulation-app-9dnaemnx8tpuappyoc6c28.streamlit.app"):
        self.api_key = api_key
        self.domain = domain
        self.geocode_url = "https://api.vworld.kr/req/address"
        self.search_url = "https://api.vworld.kr/req/search"
        self.data_url = "https://api.vworld.kr/req/data"

    def _get_headers(self) -> Dict[str, str]:
        return {"Referer": f"https://{self.domain}"}

    def geocode(self, address: str) -> Dict[str, Any]:
        """주소를 지오코딩하여 좌표, PNU, 정제주소, 행정구역 체계를 반환"""
        address = address.strip()
        
        # 전국 시·도 축약어 자동 정규화 (브이월드 API 필수 요구사항)
        sido_mapping = {
            "서울시 ": "서울특별시 ", "서울 ": "서울특별시 ",
            "부산시 ": "부산광역시 ", "부산 ": "부산광역시 ",
            "대구시 ": "대구광역시 ", "대구 ": "대구광역시 ",
            "인천시 ": "인천광역시 ", "인천 ": "인천광역시 ",
            "광주시 ": "광주광역시 ", "광주 ": "광주광역시 ",
            "대전시 ": "대전광역시 ", "대전 ": "대전광역시 ",
            "울산시 ": "울산광역시 ", "울산 ": "울산광역시 ",
            "세종시 ": "세종특별자치시 ", "세종 ": "세종특별자치시 ",
            "제주시 ": "제주특별자치도 ", "제주 ": "제주특별자치도 ",
            "경기도 ": "경기도 ", "경기 ": "경기도 ",
            "강원도 ": "강원특별자치도 ", "강원 ": "강원특별자치도 ",
            "충북 ": "충청북도 ", "충남 ": "충청남도 ",
            "전북 ": "전북특별자치도 ", "전남 ": "전라남도 ",
            "경북 ": "경상북도 ", "경남 ": "경상남도 "
        }
        
        for short_name, full_name in sido_mapping.items():
            if address.startswith(short_name):
                address = address.replace(short_name, full_name, 1)
                break

        headers = self._get_headers()
        
        # 1차 시도: PARCEL (지번)
        params = {
            "service": "address",
            "request": "getcoord",
            "version": "2.0",
            "crs": "epsg:4326",
            "address": address,
            "refine": "true",
            "simple": "false",
            "format": "json",
            "type": "PARCEL",
            "key": self.api_key,
            "domain": self.domain
        }
        try:
            resp = requests.get(self.geocode_url, params=params, headers=headers, timeout=8)
            data = resp.json()
            if data.get("response", {}).get("status") == "OK":
                return self._parse_geocode_result(data, address)
        except Exception as e:
            pass

        # 2차 시도: ROAD (도로명)
        params["type"] = "ROAD"
        try:
            resp = requests.get(self.geocode_url, params=params, headers=headers, timeout=8)
            data = resp.json()
            if data.get("response", {}).get("status") == "OK":
                return self._parse_geocode_result(data, address)
        except Exception as e:
            pass

        # 3차 시도: Search API 2.0
        return self._search_fallback(address)

    def _parse_geocode_result(self, data: Dict[str, Any], raw_addr: str) -> Dict[str, Any]:
        resp_data = data.get("response", {})
        refined = resp_data.get("refined", {})
        structure = refined.get("structure", {})
        point = resp_data.get("result", {}).get("point", {})

        x = float(point.get("x", 0.0))
        y = float(point.get("y", 0.0))
        pnu = structure.get("level4LC") or ""

        # PNU가 지오코더에서 비어있으면 검색 API로 보완 시도
        if not pnu or len(pnu) < 19:
            search_res = self._search_fallback(refined.get("text", raw_addr))
            if search_res.get("pnu"):
                pnu = search_res["pnu"]

        return {
            "success": True,
            "raw_address": raw_addr,
            "refined_address": refined.get("text") or raw_addr,
            "pnu": pnu,
            "x": x,
            "y": y,
            "sido": structure.get("level1", ""),
            "sigg": structure.get("level2", ""),
            "emd": structure.get("level4L", ""),
            "detail_jibun": structure.get("level5", ""),
            "zipcode": structure.get("zipcode", "")
        }

    def _search_fallback(self, query: str) -> Dict[str, Any]:
        headers = self._get_headers()
        params = {
            "service": "search",
            "request": "search",
            "version": "2.0",
            "crs": "EPSG:4326",
            "size": "5",
            "page": "1",
            "query": query,
            "type": "address",
            "category": "parcel",
            "format": "json",
            "key": self.api_key,
            "domain": self.domain
        }
        try:
            resp = requests.get(self.search_url, params=params, headers=headers, timeout=8)
            data = resp.json()
            if data.get("response", {}).get("status") == "OK":
                items = data.get("response", {}).get("result", {}).get("items", [])
                if items:
                    it = items[0]
                    addr = it.get("address", {})
                    pt = it.get("point", {})
                    pnu = it.get("id", "")
                    parcel_txt = addr.get("parcel", "")
                    tokens = parcel_txt.split()
                    sido = tokens[0] if len(tokens) > 0 else ""
                    sigg = tokens[1] if len(tokens) > 1 else ""
                    emd = tokens[2] if len(tokens) > 2 else ""

                    return {
                        "success": True,
                        "raw_address": query,
                        "refined_address": parcel_txt or addr.get("road", query),
                        "pnu": pnu,
                        "x": float(pt.get("x", 0.0)),
                        "y": float(pt.get("y", 0.0)),
                        "sido": sido,
                        "sigg": sigg,
                        "emd": emd,
                        "detail_jibun": "",
                        "zipcode": addr.get("zipcode", "")
                    }
        except Exception:
            pass

        return {
            "success": False,
            "raw_address": query,
            "error": "주소를 찾을 수 없습니다. 도로명 또는 지번 주소를 확인해주세요."
        }

    def get_land_use_and_restrictions(self, x: float, y: float) -> Dict[str, Any]:
        """좌표(WGS84 lon, lat)를 기준으로 용도지역 및 각종 규제/구역을 조회"""
        geom_filter = f"POINT({x} {y})"

        # 1. 용도지역 (도시지역 우선, 관리/농림/자연환경보전 fallback)
        zoning_names = []
        for layer in ["LT_C_UQ111", "LT_C_UQ112", "LT_C_UQ113", "LT_C_UQ114"]:
            res = self._query_feature(layer, geom_filter)
            if res:
                for f in res:
                    uname = f.get("properties", {}).get("uname")
                    if uname and uname not in zoning_names:
                        zoning_names.append(uname)
                if zoning_names:
                    break

        # 2. 지구단위계획구역
        district_plan_names = []
        res_dp = self._query_feature("LT_C_UPISUQ161", geom_filter)
        is_district_plan = False
        if res_dp:
            is_district_plan = True
            for f in res_dp:
                uname = f.get("properties", {}).get("uname") or f.get("properties", {}).get("name")
                if uname and uname not in district_plan_names:
                    district_plan_names.append(uname)

        # 3. 용도지구 (경관지구, 고도지구, 방화지구 등)
        overlay_zones = []
        for l in ["LT_C_UPISUQ151", "LT_C_UQ121", "LT_C_UQ123", "LT_C_UQ124", "LT_C_UQ126", "LT_C_UQ128"]:
            res_oz = self._query_feature(l, geom_filter)
            if res_oz:
                for f in res_oz:
                    uname = f.get("properties", {}).get("uname") or f.get("properties", {}).get("name")
                    if uname and uname not in overlay_zones:
                        overlay_zones.append(uname)

        # 4. 기타 규제구역 (토지거래허가구역, 개발행위허가제한 등)
        restrictions = []
        for l in ["LT_C_UQ141", "LT_C_UPISUQ171"]:
            res_r = self._query_feature(l, geom_filter)
            if res_r:
                for f in res_r:
                    uname = f.get("properties", {}).get("uname") or f.get("properties", {}).get("name")
                    if uname and uname not in restrictions:
                        restrictions.append(uname)

        primary_zoning = zoning_names[0] if zoning_names else "미지정 (또는 용도지역 확인 필요)"

        return {
            "zoning_list": zoning_names,
            "primary_zoning": primary_zoning,
            "is_district_plan": is_district_plan,
            "district_plan_names": district_plan_names,
            "overlay_zones": overlay_zones,
            "restrictions": restrictions
        }

    def get_official_cadastral_info(self, pnu: str) -> Dict[str, Any]:
        """PNU를 기반으로 토지특성 및 토지대장 공부상 대지면적, 지목 등 조회"""
        if not pnu or len(pnu) < 10:
            return {"has_cadastral": False}

        url = "http://api.vworld.kr/ned/data/getLandCharacteristics"
        headers = self._get_headers()
        params = {
            "key": self.api_key,
            "domain": self.domain,
            "pnu": pnu,
            "format": "json",
            "numOfRows": 1
        }
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=6)
            data = resp.json()
            fields = data.get("landCharacteristicss", {}).get("field", [])
            if fields:
                f = fields[0]
                area_val = float(f.get("lndpclAr", 0.0) or 0.0)
                price_val = f.get("pblntfPclnd") or ""
                if price_val and str(price_val).isdigit():
                    price_str = f"{int(price_val):,} 원/㎡"
                else:
                    price_str = f"{price_val} 원/㎡" if price_val else "미공시"

                return {
                    "has_cadastral": True,
                    "official_area_sqm": area_val,
                    "official_area_py": round(area_val / 3.305785, 1),
                    "jimok": f.get("lndcgrCodeNm", "대"),
                    "land_use_situation": f.get("ladUseSittnNm", "주거용"),
                    "road_side": f.get("roadSideCodeNm", "중로각지"),
                    "topography_height": f.get("tpgrphHgCodeNm", "평지"),
                    "topography_shape": f.get("tpgrphFrmCodeNm", "부정형"),
                    "official_price": price_str,
                    "stdr_year": f.get("stdrYear", "2024")
                }
        except Exception:
            pass

        return {"has_cadastral": False}

    def _query_feature(self, layer: str, geom_filter: str) -> Optional[List[Dict[str, Any]]]:
        headers = self._get_headers()
        params = {
            "service": "data",
            "request": "GetFeature",
            "data": layer,
            "key": self.api_key,
            "domain": self.domain,
            "geomFilter": geom_filter,
            "geometry": "false",
            "crs": "EPSG:4326",
            "format": "json"
        }
        try:
            resp = requests.get(self.data_url, params=params, headers=headers, timeout=6)
            data = resp.json()
            if data.get("response", {}).get("status") == "OK":
                return data.get("response", {}).get("result", {}).get("featureCollection", {}).get("features", [])
        except Exception:
            pass
        return None