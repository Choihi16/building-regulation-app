"""
행정안전부 주소정보 API 및 V-World 연동 클라이언트 모듈 (전국 17개 시·도 검색 보정 강화)
"""

import requests
import json
import re
from typing import Dict, Any, List, Optional

MOIS_API_KEY = "devU01TX0FVVEgyMDI2MTAxMzE0NTg0NTEyMDY4NDM="
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
        """주소 입력값 자동 클렌징 및 전국 시·도 생략 자동 보정"""
        address = address.strip()
        address = re.sub(r'번지', '', address).strip()
        address = re.sub(r'\s+', ' ', address)
        address = address.replace("제물포구", "중구")

        # 전국 단위 주요 동/지역명에 따른 시·도·구 자동 매칭 딕셔너리
        auto_sido_mapping = {
            # 충청남도
            "불당동": "충청남도 천안시 서북구 ", "백석동": "충청남도 천안시 서북구 ", "두정동": "충청남도 천안시 서북구 ", "성정동": "충청남도 천안시 서북구 ",
            "신부동": "충청남도 천안시 동남구 ", "청당동": "충청남도 천안시 동남구 ", "봉명동": "충청남도 천안시 동남구 ",
            "배방읍": "충청남도 아산시 ", "탕정면": "충청남도 아산시 ", "모종동": "충청남도 아산시 ", "용화동": "충청남도 아산시 ",
            "서산": "충청남도 서산시 ", "당진": "충청남도 당진시 ", "홍성": "충청남도 홍성군 ", "예산": "충청남도 예산군 ", "공주": "충청남도 공주시 ",
            # 충청북도
            "복대동": "충청북도 청주시 흥덕구 ", "가경동": "충청북도 청주시 흥덕구 ", "오창읍": "충청북도 청주시 청원구 ",
            "용암동": "충청북도 청주시 상당구 ", "성화동": "충청북도 청주시 서원구 ",
            "충주": "충청북도 충주시 ", "제천": "충청북도 제천시 ", "음성": "충청북도 음성군 ", "진천": "충청북도 진천군 ",
            # 전라남도
            "오림동": "전라남도 여수시 ", "웅천동": "전라남도 여수시 ", "국동": "전라남도 여수시 ",
            "옥암동": "전라남도 목포시 ", "하당동": "전라남도 목포시 ",
            "조례동": "전라남도 순천시 ", "연향동": "전라남도 순천시 ", "왕지동": "전라남도 순천시 ",
            "나주": "전라남도 나주시 ", "광양": "전라남도 광양시 ", "무안": "전라남도 무안군 ", "남악": "전라남도 무안군 ",
            # 전라북도 (전북특별자치도)
            "효자동": "전북특별자치도 전주시 완산구 ", "중화산동": "전북특별자치도 전주시 완산구 ", "서신동": "전북특별자치도 전주시 완산구 ",
            "송천동": "전북특별자치도 전주시 덕진구 ", "인후동": "전북특별자치도 전주시 덕진구 ", "혁신": "전북특별자치도 전주시 완산구 ",
            "영등동": "전북특별자치도 익산시 ", "모현동": "전북특별자치도 익산시 ",
            "수송동": "전북특별자치도 군산시 ", "나운동": "전북특별자치도 군산시 ",
            "정읍": "전북특별자치도 정읍시 ", "남원": "전북특별자치도 남원시 ", "김제": "전북특별자치도 김제시 ",
            # 경상남도
            "중앙동": "경상남도 창원시 성산구 ", "상남동": "경상남도 창원시 성산구 ", "용호동": "경상남도 창원시 성산구 ",
            "내서읍": "경상남도 창원시 마산회원구 ", "가은": "경상남도 창원시 의창구 ",
            "삼문동": "경상남도 밀양시 ", "거제": "경상남도 거제시 ", "통영": "경상남도 통영시 ", "진주": "경상남도 진주시 ", "김해": "경상남도 김해시 ", "양산": "경상남도 양산시 ",
            # 경상북도
            "상대동": "경상북도 포항시 남구 ", "장성동": "경상북도 포항시 북구 ", "양덕동": "경상북도 포항시 북구 ",
            "황성동": "경상북도 경주시 ", "용강동": "경상북도 경주시 ",
            "구미": "경상북도 구미시 ", "김천": "경상북도 김천시 ", "안동": "경상북도 안동시 ", "영주": "경상북도 영주시 ", "경산": "경상북도 경산시 ",
            # 기타 주요 지역
            "신흥동": "인천광역시 중구 ", "구월동": "인천광역시 남동구 ", "우동": "부산광역시 해운대구 ",
            "정자동": "경기도 성남시 분당구 ", "길음동": "서울특별시 성북구 "
        }

        has_sido_included = any(sido in address for sido in [
            "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", 
            "경기", "강원", "충북", "충청북", "충남", "충청남", "전북", "전라북", 
            "전남", "전라남", "경북", "경상북", "경남", "경상남", "제주"
        ])

        if not has_sido_included:
            for keyword, prefix in auto_sido_mapping.items():
                if keyword in address:
                    address = prefix + address
                    break

        # 표준 시·도 축약어 정규화
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
            "충북 ": "충청북도 ", "충청북도 ": "충청북도 ",
            "충남 ": "충청남도 ", "충청남도 ": "충청남도 ",
            "전북 ": "전북특별자치도 ", "전라북도 ": "전북특별자치도 ",
            "전남 ": "전라남도 ", "전라남도 ": "전라남도 ",
            "경북 ": "경상북도 ", "경상북도 ": "경상북도 ",
            "경남 ": "경상남도 ", "경상남도 ": "경상남도 "
        }

        for short_name, full_name in sido_mapping.items():
            if address.startswith(short_name):
                address = address.replace(short_name, full_name, 1)
                break

        return address

    def search_address_candidates(self, keyword: str) -> List[Dict[str, Any]]:
        """입력 키워드에 연관된 전국 주소 후보 목록 반환"""
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