"""
행정안전부 주소정보 API 및 V-World 연동 클라이언트 모듈
- 연관 주소 후보 리스트 반환 (search_address_candidates) 지원
- 스트림릿 클라우드 IP 차단 방지 및 지번/도로명 완벽 지원
"""

import requests
import json
import re
from typing import Dict, Any, List, Optional

# 공공데이터포털 행정안전부 주소 API 인증키
MOIS_API_KEY = "devU01TX0FVVEgyMDI2MTAxMzE0NTg0NTEyMDY4NDM="
# V-World API 인증키 (용도지역 및 대장 조회용)
VWORLD_KEY = "9FF03DCA-70F5-41A0-AC8B-0EB520A612B0"

class VWorldClient:
    def __init__(self, api_key: str = MOIS_API_KEY, domain: str = "building-regulation-app-9dnaemnx8tpuappyoc6c28.streamlit.app"):
        self.api_key = api_key
        self.domain = domain
        self.addr_api_url = "https://www.juso.go.kr/addrlink/addrLinkApi.do"
        self.data_url = "https://api.vworld.kr/req/data"

    def _get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def _clean_address(self, address: str) -> str:
        """주소 입력값 자동 클렌징 및 정규화"""
        address = address.strip()
        address = re.sub(r'번지', '', address).strip()
        address = re.sub(r'\s+', ' ', address)
        address = address.replace("제물포구", "중구")

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

        return address

    def search_address_candidates(self, keyword: str) -> List[Dict[str, Any]]:
        """입력 키워드에 연관된 주소 후보 목록 반환 (드롭다운 UI용)"""
        if not keyword or len(keyword.strip()) < 2:
            return []

        cleaned_kw = self._clean_address(keyword)
        params = {
            "confmKey": self.api_key,
            "currentPage": "1",
            "countPerPage": "10",
            "keyword": cleaned_kw,
            "resultType": "json"
        }

        try:
            resp = requests.get(self.addr_api_url, params=params, timeout=6)
            data = resp.json()
            juso_list = data.get("results", {}).get("juso", [])

            candidates = []
            for item in juso_list:
                road_addr = item.get("roadAddr", "")
                jibun_addr = item.get("jibunAddr", "")
                adm_cd = item.get("admCd", "")

                jibun_tokens = jibun_addr.split()
                sido = jibun_tokens[0] if len(jibun_tokens) > 0 else ""
                sigg = jibun_tokens[1] if len(jibun_tokens) > 1 else ""
                emd = jibun_tokens[2] if len(jibun_tokens) > 2 else ""

                ln_mn = str(item.get("lnMnnm", "0")).zfill(4)
                ln_sl = str(item.get("lnSlno", "0")).zfill(4)
                san_yn = "2" if "산" in jibun_addr else "1"
                pnu = f"{adm_cd}{san_yn}{ln_mn}{ln_sl}" if len(adm_cd) == 10 else ""

                candidates.append({
                    "refined_address": jibun_addr or road_addr,
                    "road_address": road_addr,
                    "jibun_address": jibun_addr,
                    "pnu": pnu,
                    "sido": sido,
                    "sigg": sigg,
                    "emd": emd,
                    "zipcode": item.get("zipNo", "")
                })
            return candidates
        except Exception:
            return []

    def geocode(self, address: str) -> Dict[str, Any]:
        """주소 지오코딩 및 좌표, PNU 추출"""
        candidates = self.search_address_candidates(address)
        if not candidates:
            return {
                "success": False,
                "raw_address": address,
                "error": "검색된 주소가 없습니다. 정확한 지번이나 도로명으로 입력해 주세요."
            }

        item = candidates[0]
        x, y = self._get_coords_from_vworld(item["refined_address"])

        return {
            "success": True,
            "raw_address": address,
            "refined_address": item["refined_address"],
            "pnu": item["pnu"],
            "x": x,
            "y": y,
            "sido": item["sido"],
            "sigg": item["sigg"],
            "emd": item["emd"],
            "detail_jibun": "",
            "zipcode": item["zipcode"]
        }

    def _get_coords_from_vworld(self, query: str) -> tuple:
        """좌표 매칭을 위한 브이월드 보조 호출"""
        url = "https://api.vworld.kr/req/search"
        params = {
            "service": "search",
            "request": "search",
            "version": "2.0",
            "crs": "EPSG:4326",
            "size": "1",
            "query": query,
            "type": "address",
            "category": "parcel",
            "format": "json",
            "key": VWORLD_KEY
        }
        try:
            session = requests.Session()
            session.headers.update({"User-Agent": "Mozilla/5.0"})
            resp = session.get(url, params=params, timeout=5)
            data = resp.json()
            items = data.get("response", {}).get("result", {}).get("items", [])
            if items:
                pt = items[0].get("point", {})
                return float(pt.get("x", 0.0)), float(pt.get("y", 0.0))
        except Exception:
            pass
        return 126.9780, 37.5665

    def get_land_use_and_restrictions(self, x: float, y: float) -> Dict[str, Any]:
        geom_filter = f"POINT({x} {y})"
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

        district_plan_names = []
        res_dp = self._query_feature("LT_C_UPISUQ161", geom_filter)
        is_district_plan = False
        if res_dp:
            is_district_plan = True
            for f in res_dp:
                uname = f.get("properties", {}).get("uname") or f.get("properties", {}).get("name")
                if uname and uname not in district_plan_names:
                    district_plan_names.append(uname)

        overlay_zones = []
        for l in ["LT_C_UPISUQ151", "LT_C_UQ121", "LT_C_UQ123", "LT_C_UQ124", "LT_C_UQ126", "LT_C_UQ128"]:
            res_oz = self._query_feature(l, geom_filter)
            if res_oz:
                for f in res_oz:
                    uname = f.get("properties", {}).get("uname") or f.get("properties", {}).get("name")
                    if uname and uname not in overlay_zones:
                        overlay_zones.append(uname)

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
        if not pnu or len(pnu) < 10:
            return {"has_cadastral": False}

        url = "http://api.vworld.kr/ned/data/getLandCharacteristics"
        headers = self._get_headers()
        params = {
            "key": VWORLD_KEY,
            "domain": self.domain,
            "pnu": pnu,
            "format": "json",
            "numOfRows": 1
        }
        try:
            session = requests.Session()
            session.headers.update(headers)
            resp = session.get(url, params=params, timeout=6)
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
            "key": VWORLD_KEY,
            "domain": self.domain,
            "geomFilter": geom_filter,
            "geometry": "false",
            "crs": "EPSG:4326",
            "format": "json"
        }
        try:
            session = requests.Session()
            session.headers.update(headers)
            resp = session.get(self.data_url, params=params, timeout=6)
            data = resp.json()
            if data.get("response", {}).get("status") == "OK":
                return data.get("response", {}).get("result", {}).get("featureCollection", {}).get("features", [])
        except Exception:
            pass
        return None