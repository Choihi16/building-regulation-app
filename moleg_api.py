"""
법제처 자치법규 Open API 클라이언트 모듈
- OC: usun7557
- 도시계획조례, 건축조례 검색 및 상세 조문(건폐율, 용적률, 최고높이, 심의규정) 추출
"""

import requests
import xmltodict
import re
from typing import Dict, Any, List, Optional, Tuple

MOLEG_OC = "usun7557"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.law.go.kr"
}

class MolegClient:
    def __init__(self, oc: str = MOLEG_OC):
        self.oc = oc
        self.search_url = "https://www.law.go.kr/DRF/lawSearch.do"
        self.service_url = "https://www.law.go.kr/DRF/lawService.do"
        self._cache: Dict[str, Any] = {}

    def search_ordinance(self, query: str, target_org: Optional[str] = None, exact_title: Optional[str] = None, display: int = 50) -> List[Dict[str, Any]]:
        """자치법규 목록 검색"""
        cache_key = f"search_{query}_{target_org}_{display}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        params = {
            "OC": self.oc,
            "target": "ordin",
            "type": "XML",
            "query": query,
            "display": display
        }
        try:
            resp = requests.get(self.search_url, params=params, headers=HEADERS, timeout=8)
            data = xmltodict.parse(resp.content.decode("utf-8"))
            laws = data.get("OrdinSearch", {}).get("law", [])
            if isinstance(laws, dict):
                laws = [laws]

            # 우선순위 정렬 및 필터링
            filtered = []
            for l in laws:
                title = l.get("자치법규명", "").strip()
                org = l.get("지자체기관명", "").strip()

                # 정확한 제목 매칭 우선
                score = 0
                if exact_title and title == exact_title:
                    score += 100
                elif exact_title and exact_title in title:
                    score += 50

                if target_org and target_org in org:
                    score += 30

                l["_match_score"] = score
                filtered.append(l)

            filtered.sort(key=lambda x: x["_match_score"], reverse=True)
            self._cache[cache_key] = filtered
            return filtered
        except Exception as e:
            return []

    def get_ordinance_detail(self, mst: str) -> Optional[Dict[str, Any]]:
        """MST 일련번호로 자치법규 상세 본문(조문, 부칙, 별표 등) 조회"""
        if mst in self._cache:
            return self._cache[mst]

        params = {
            "OC": self.oc,
            "target": "ordin",
            "MST": mst,
            "type": "XML"
        }
        try:
            resp = requests.get(self.service_url, params=params, headers=HEADERS, timeout=8)
            data = xmltodict.parse(resp.content.decode("utf-8"))
            law_service = data.get("LawService", {})
            if not law_service:
                return None

            basic_info = law_service.get("자치법규기본정보", {})
            articles = law_service.get("조문", {}).get("조", [])
            if isinstance(articles, dict):
                articles = [articles]

            parsed = {
                "mst": mst,
                "title": basic_info.get("자치법규명", ""),
                "org": basic_info.get("지자체기관명", ""),
                "enforce_date": basic_info.get("시행일자", ""),
                "articles": articles
            }
            self._cache[mst] = parsed
            return parsed
        except Exception:
            return None

    def find_relevant_articles(self, articles: List[Dict[str, Any]], keywords: List[str]) -> List[Dict[str, Any]]:
        """조문 목록에서 특정 키워드가 포함된 조문 추출"""
        matched = []
        for a in articles:
            title = str(a.get("조제목", "") or "")
            content = str(a.get("조내용", "") or "")
            if any(k in title for k in keywords) or any(k in content for k in keywords):
                matched.append({
                    "num": a.get("조문번호", ""),
                    "title": title,
                    "content": content
                })
        return matched

    def get_municipal_ordinance_bundle(self, sido: str, sigg: str) -> Dict[str, Any]:
        """시도 및 시군구 명칭에 부합하는 도시계획조례 및 건축조례 세트 조회"""
        bundle = {
            "planning_ordinance": None,
            "building_ordinance": None,
            "bcr_articles": [],
            "far_articles": [],
            "height_articles": [],
            "deliberation_articles": []
        }

        # 1. 도시계획조례 탐색 (광역 우선, 시/군일 경우 시군 우선)
        is_metro = any(m in sido for m in ["특별시", "광역시", "특별자치시", "특별자치도"])
        
        # 검색 대상 지자체명 결정
        if is_metro:
            planning_org = sido.strip()
            planning_query = f"{sido} 도시계획 조례"
        else:
            city_name = sigg.split()[0] if sigg else sido
            planning_org = city_name.strip()
            planning_query = f"{city_name} 도시계획 조례"

        planning_list = self.search_ordinance(planning_query, target_org=planning_org, display=50)
        selected_planning = None

        # 1차: 기관명 완전 일치 및 제목이 '[시도] 도시계획 조례'인 것 최우선
        exact_title_clean = f"{planning_org}도시계획조례".replace(" ", "")
        for l in planning_list:
            t = l.get("자치법규명", "").replace(" ", "")
            org = l.get("지자체기관명", "").strip()
            if org == planning_org and t == exact_title_clean:
                selected_planning = l
                break

        # 2차: 기관명 완전 일치하면서 도시계획조례 포함
        if not selected_planning:
            for l in planning_list:
                t = l.get("자치법규명", "").replace(" ", "")
                org = l.get("지자체기관명", "").strip()
                if org == planning_org and "도시계획조례" in t and "시행규칙" not in t and "위원회" not in t:
                    selected_planning = l
                    break

        # 3차: fallback
        if not selected_planning:
            for l in planning_list:
                t = l.get("자치법규명", "").replace(" ", "")
                if "도시계획조례" in t and "시행규칙" not in t and "위원회" not in t:
                    selected_planning = l
                    break
        if not selected_planning and planning_list:
            selected_planning = planning_list[0]

        if selected_planning:
            mst = selected_planning.get("자치법규일련번호")
            det = self.get_ordinance_detail(mst)
            if det:
                bundle["planning_ordinance"] = det
                bundle["bcr_articles"] = self.find_relevant_articles(det["articles"], ["건폐율"])
                bundle["far_articles"] = self.find_relevant_articles(det["articles"], ["용적률"])

        # 2. 건축조례 탐색 (기초 지자체 또는 광역)
        # 우선 시군구 건축조례 검색, 없으면 광역 건축조례
        bld_query = f"{sigg} 건축 조례" if sigg else f"{sido} 건축 조례"
        bld_list = self.search_ordinance(bld_query, target_org=sigg if sigg else sido, display=40)
        
        selected_bld = None
        for l in bld_list:
            t = l.get("자치법규명", "").replace(" ", "")
            if "건축조례" in t and "시행규칙" not in t and "특별회계" not in t and "지원" not in t:
                selected_bld = l
                break

        # 구 조례에서 못 찾으면 광역(서울특별시 등) 건축조례 검색
        if not selected_bld:
            bld_list_sido = self.search_ordinance(f"{sido} 건축 조례", target_org=sido, display=40)
            for l in bld_list_sido:
                t = l.get("자치법규명", "").replace(" ", "")
                if "건축조례" in t and "시행규칙" not in t and "특별회계" not in t:
                    selected_bld = l
                    break

        if selected_bld:
            mst = selected_bld.get("자치법규일련번호")
            det = self.get_ordinance_detail(mst)
            if det:
                bundle["building_ordinance"] = det
                bundle["height_articles"] = self.find_relevant_articles(det["articles"], ["높이", "일조", "가로구역"])
                bundle["deliberation_articles"] = self.find_relevant_articles(det["articles"], ["심의", "위원회"])

        return bundle
