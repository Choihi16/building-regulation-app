"""
행정안전부 주소정보 조회 API 클라이언트 모듈 (오타 수정본)
- 지번 및 도로명 주소 통합 검색 -> PNU 및 행정구역 추출
- 용도지역 및 대장 조회는 기존 V-World 데이터 API 연동 유지
"""

import requests
import json
from typing import Dict, Any, List, Optional

# 발급받으신 공공데이터포털 인증키
MOIS_API_KEY = "devU01TX0FVVEgyMDI2MTAxMzE0NTg0NTEyMDY4NDM="
VWORLD_KEY = "9FF03DCA-70F5-41A0-AC8B-0EB520A612B0"

class VWorldClient:
    def __init__(self, api_key: str = MOIS_API_KEY, domain: str = "building-regulation-app-9dnaemnx8tpuappyoc6c28.streamlit.app"):
        self.api_key = api_key
        self.domain = domain
        # 행정안전부 도로명주소/지번 통합 검색 API
        self.addr_api_url = "https://www.juso.go.kr/addrlink/addrLinkApi.do"
        self.data_url = "https://api.vworld.kr/req/data"

    def _get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def geocode(self, address: str) -> Dict[str, Any]:
        """행정안전부 API를 활용하여 지번/도로명 주소 검색, PNU 및 행정구역 추출"""
        address = address.strip()
        
        # 시·도 축약어 정규화
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

        params = {
            "confmKey": self.api_key,
            "currentPage": "1",
            "countPerPage": "5",
            "keyword": address,
            "resultType": "json"
        }

        try:
            resp = requests.get(self.addr_api_url, params=params, timeout=8)
            data = resp.json()
            
            common = data.get("results", {}).get("common", {})
            error_code = common.get("errorCode")
            
            if error_code != "0":
                return {
                    "success": False,
                    "raw_address": address,
                    "error": f"주소 API 오류 [{error_code}]: {common.get('errorMessage')}"
                }

            juso_list = data.get("results", {}).get("juso", [])
            if not juso_list:
                return {
                    "success": False,
                    "raw_address": address,
                    "error": "검색된 주소가 없습니다. 정확한 지번이나 도로명으로 입력해 주세요."
                }

            # 첫 번째 검색 결과 활용
            item = juso_list[0]
            road_addr = item.get("roadAddr", "")
            jibun_addr = item.get("jibunAddr", "")
            adm_cd = item.get("admCd", "") # 행정구역 코드 (10자리)
            
            # 지번 정보 분리
            jibun_tokens = jibun_addr.split()
            sido = jibun_tokens[0] if len(jibun_tokens) > 0 else ""
            sigg = jibun_tokens[1] if len(jibun_tokens) > 1 else ""
            emd = jibun_tokens[2] if len(jibun_tokens) > 2 else ""
            
            # PNU 생성 (시군구코드(5) + 읍면동리코드(5) + 산여부(1) + 본번(4) + 부번(4))
            ln_mn = str(item.get("lnMnnm", "0")).zfill(4)
            ln_sl = str(item.get("lnSlno", "0")).zfill(4)
            san_yn = "2" if "산" in jibun_addr else "1"
            pnu = f"{adm_cd}{san_yn}{ln_mn}{ln_sl}" if len(adm_cd) == 10 else ""

            # 좌표 조회를 위해 V-World 검색 API 보조 연동
            x, y = self._get_coords_from_vworld(road_addr or jibun_addr)

            return {
                "success": True,
                "raw_address": address,
                "refined_address": road_addr or jibun_addr,
                "pnu": pnu,
                "x": x,
                "y": y,
                "sido": sido,
                "sigg": sigg,
                "emd": emd,
                "detail_jibun": "",
                "zipcode": item.get("zipNo", "")
            }

        except Exception as e:
            return {
                "success": False,
                "raw_address": address,
                "error": f"통신 예외 발생: {str(e)}"
            }

    def _get_coords_from_vworld(self, query: str) -> tuple:
        """좌표 매칭을 위한 브이월드 검색 API 보조 호출"""
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
        return 0.0, 0.0

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