"""
건축 법규 및 기획설계 분석 엔진 (Regulation & Feasibility Engine)
- 국토계획법 및 지자체 자치법규(도시계획조례, 건축조례, 주차장조례) 연동
- 대지면적 검증 (공부상 토지대장 면적 대조)
- 계획 용도별(공동주택, 주상복합, 오피스텔 등) 타입별 세대구성 및 미정 시 자동 추정
- 4대 심의(건축/소방/교통/경관) O/X 자동 판정 및 리스크 평가
- 지구단위계획 실무 체크리스트 표 (항목별 규정, 점검사항, 인센티브 조건)
- 임원진/경영진 보고용 3줄 결론 및 사업성 지표 도출
"""

from typing import Dict, Any, List, Optional, Tuple
import math
import re

# 국토계획법 시행령 및 주요 지자체 표준 법정 상한 매핑 DB
STATUTORY_LIMITS_DB = {
    "제1종전용주거지역": {
        "bcr_national": "50% 이하",
        "bcr_national_num": 50.0,
        "bcr_ordinance_seoul": "50%",
        "bcr_ordinance_incheon": "50%",
        "bcr_num": 50.0,
        "far_national": "50% 이상 100% 이하",
        "far_national_num": 100.0,
        "far_ordinance_seoul": "100%",
        "far_ordinance_incheon": "100%",
        "far_num": 100.0,
        "desc": "단독주택 중심의 양호한 주거환경을 보호하기 위하여 필요한 지역"
    },
    "제2종전용주거지역": {
        "bcr_national": "50% 이하",
        "bcr_national_num": 50.0,
        "bcr_ordinance_seoul": "40%",
        "bcr_ordinance_incheon": "50%",
        "bcr_num": 40.0,
        "far_national": "100% 이상 150% 이하",
        "far_national_num": 150.0,
        "far_ordinance_seoul": "120%",
        "far_ordinance_incheon": "150%",
        "far_num": 120.0,
        "desc": "공동주택 중심의 양호한 주거환경을 보호하기 위하여 필요한 지역"
    },
    "제1종일반주거지역": {
        "bcr_national": "60% 이하",
        "bcr_national_num": 60.0,
        "bcr_ordinance_seoul": "60%",
        "bcr_ordinance_incheon": "60%",
        "bcr_num": 60.0,
        "far_national": "100% 이상 200% 이하",
        "far_national_num": 200.0,
        "far_ordinance_seoul": "150%",
        "far_ordinance_incheon": "150%",
        "far_num": 150.0,
        "desc": "저층주택(4층 이하)을 중심으로 편리한 주거환경을 조성하기 위하여 필요한 지역"
    },
    "제2종일반주거지역": {
        "bcr_national": "60% 이하",
        "bcr_national_num": 60.0,
        "bcr_ordinance_seoul": "60%",
        "bcr_ordinance_incheon": "60%",
        "bcr_num": 60.0,
        "far_national": "100% 이상 250% 이하",
        "far_national_num": 250.0,
        "far_ordinance_seoul": "200%",
        "far_ordinance_incheon": "250%",
        "far_num": 200.0,
        "desc": "중층주택을 중심으로 편리한 주거환경을 조성하기 위하여 필요한 지역"
    },
    "제3종일반주거지역": {
        "bcr_national": "50% 이하",
        "bcr_national_num": 50.0,
        "bcr_ordinance_seoul": "50%",
        "bcr_ordinance_incheon": "50%",
        "bcr_num": 50.0,
        "far_national": "100% 이상 300% 이하",
        "far_national_num": 300.0,
        "far_ordinance_seoul": "250%",
        "far_ordinance_incheon": "300%",
        "far_num": 250.0,
        "desc": "중고층주택을 중심으로 편리한 주거환경을 조성하기 위하여 필요한 지역"
    },
    "준주거지역": {
        "bcr_national": "70% 이하",
        "bcr_national_num": 70.0,
        "bcr_ordinance_seoul": "60%",
        "bcr_ordinance_incheon": "60%",
        "bcr_num": 60.0,
        "far_national": "200% 이상 500% 이하",
        "far_national_num": 500.0,
        "far_ordinance_seoul": "400%",
        "far_ordinance_incheon": "300% (주상복합 300% / 상업 350%)",
        "far_num": 400.0,
        "desc": "주거기능을 위주로 이를 지원하는 일부 상업기능 및 업무기능을 보완하기 위하여 필요한 지역"
    },
    "중심상업지역": {
        "bcr_national": "90% 이하",
        "bcr_national_num": 90.0,
        "bcr_ordinance_seoul": "60%",
        "bcr_ordinance_incheon": "80% (주거복합 70%)",
        "bcr_num": 60.0,
        "far_national": "400% 이상 1,500% 이하",
        "far_national_num": 1500.0,
        "far_ordinance_seoul": "1,000% (서울도심 800%)",
        "far_ordinance_incheon": "1,000% 이하",
        "far_num": 1000.0,
        "desc": "도심·부도심의 상업기능 및 업무기능의 확충을 위하여 필요한 지역"
    },
    "일반상업지역": {
        "bcr_national": "80% 이하",
        "bcr_national_num": 80.0,
        "bcr_ordinance_seoul": "60%",
        "bcr_ordinance_incheon": "70% 이하 (주거복합 60%)",
        "bcr_num": 60.0,
        "far_national": "300% 이상 1,300% 이하",
        "far_national_num": 1300.0,
        "far_ordinance_seoul": "800% (서울도심 600%)",
        "far_ordinance_incheon": "700% (인천시 조례 주거복합 상한 700% 제한)",
        "far_num": 800.0,
        "desc": "일반적인 상업기능 및 업무기능을 담당하기 위하여 필요한 지역"
    },
    "근린상업지역": {
        "bcr_national": "70% 이하",
        "bcr_national_num": 70.0,
        "bcr_ordinance_seoul": "60%",
        "bcr_ordinance_incheon": "70%",
        "bcr_num": 60.0,
        "far_national": "200% 이상 900% 이하",
        "far_national_num": 900.0,
        "far_ordinance_seoul": "600% (서울도심 500%)",
        "far_ordinance_incheon": "700%",
        "far_num": 600.0,
        "desc": "근린지역에서의 일용품 및 서비스의 공급을 위하여 필요한 지역"
    },
    "유통상업지역": {
        "bcr_national": "80% 이하",
        "bcr_national_num": 80.0,
        "bcr_ordinance_seoul": "60%",
        "bcr_ordinance_incheon": "70%",
        "bcr_num": 60.0,
        "far_national": "200% 이상 1,100% 이하",
        "far_national_num": 1100.0,
        "far_ordinance_seoul": "600% (서울도심 500%)",
        "far_ordinance_incheon": "800%",
        "far_num": 600.0,
        "desc": "도시내 및 지역간 유통기능의 증진을 위하여 필요한 지역"
    },
    "전용공업지역": {
        "bcr_national": "70% 이하",
        "bcr_national_num": 70.0,
        "bcr_ordinance_seoul": "60%",
        "bcr_ordinance_incheon": "70%",
        "bcr_num": 60.0,
        "far_national": "150% 이상 300% 이하",
        "far_national_num": 300.0,
        "far_ordinance_seoul": "200%",
        "far_ordinance_incheon": "250%",
        "far_num": 200.0,
        "desc": "주로 중화학공업, 공해성 공업 등을 수용하기 위하여 필요한 지역"
    },
    "일반공업지역": {
        "bcr_national": "70% 이하",
        "bcr_national_num": 70.0,
        "bcr_ordinance_seoul": "60%",
        "bcr_ordinance_incheon": "70%",
        "bcr_num": 60.0,
        "far_national": "200% 이상 350% 이하",
        "far_national_num": 350.0,
        "far_ordinance_seoul": "200%",
        "far_ordinance_incheon": "300%",
        "far_num": 200.0,
        "desc": "환경을 저해하지 아니하는 공업의 배치를 위하여 필요한 지역"
    },
    "준공업지역": {
        "bcr_national": "70% 이하",
        "bcr_national_num": 70.0,
        "bcr_ordinance_seoul": "60%",
        "bcr_ordinance_incheon": "70%",
        "bcr_num": 60.0,
        "far_national": "200% 이상 400% 이하",
        "far_national_num": 400.0,
        "far_ordinance_seoul": "400%",
        "far_ordinance_incheon": "350%",
        "far_num": 400.0,
        "desc": "경공업이나 그 밖의 공업을 수용하되, 주거기능·상업기능 및 업무기능의 보완이 필요한 지역"
    },
    "보전녹지지역": {
        "bcr_national": "20% 이하",
        "bcr_national_num": 20.0,
        "bcr_ordinance_seoul": "20%",
        "bcr_ordinance_incheon": "20%",
        "bcr_num": 20.0,
        "far_national": "50% 이상 80% 이하",
        "far_national_num": 80.0,
        "far_ordinance_seoul": "50%",
        "far_ordinance_incheon": "80%",
        "far_num": 50.0,
        "desc": "도시의 자연환경·경관·산림 및 녹지공간을 보전할 필요가 있는 지역"
    },
    "생산녹지지역": {
        "bcr_national": "20% 이하",
        "bcr_national_num": 20.0,
        "bcr_ordinance_seoul": "20%",
        "bcr_ordinance_incheon": "20%",
        "bcr_num": 20.0,
        "far_national": "50% 이상 100% 이하",
        "far_national_num": 100.0,
        "far_ordinance_seoul": "50%",
        "far_ordinance_incheon": "100%",
        "far_num": 50.0,
        "desc": "주로 농업적 생산을 위하여 개발을 유보할 필요가 있는 지역"
    },
    "자연녹지지역": {
        "bcr_national": "20% 이하",
        "bcr_national_num": 20.0,
        "bcr_ordinance_seoul": "20%",
        "bcr_ordinance_incheon": "20%",
        "bcr_num": 20.0,
        "far_national": "50% 이상 100% 이하",
        "far_national_num": 100.0,
        "far_ordinance_seoul": "50%",
        "far_ordinance_incheon": "100%",
        "far_num": 50.0,
        "desc": "도시의 녹지공간의 확보, 도시확산의 방지 등을 위하여 불가피한 경우에 한하여 제한적 개발이 허용되는 지역"
    },
    "계획관리지역": {
        "bcr_national": "40% 이하",
        "bcr_national_num": 40.0,
        "bcr_ordinance_seoul": "40%",
        "bcr_ordinance_incheon": "40%",
        "bcr_num": 40.0,
        "far_national": "50% 이상 100% 이하",
        "far_national_num": 100.0,
        "far_ordinance_seoul": "100%",
        "far_ordinance_incheon": "100%",
        "far_num": 100.0,
        "desc": "도시지역으로의 편입이 예상되는 지역 또는 제한적 이용·개발을 하려는 지역"
    },
    "생산관리지역": {
        "bcr_national": "20% 이하",
        "bcr_national_num": 20.0,
        "bcr_ordinance_seoul": "20%",
        "bcr_ordinance_incheon": "20%",
        "bcr_num": 20.0,
        "far_national": "50% 이상 80% 이하",
        "far_national_num": 80.0,
        "far_ordinance_seoul": "80%",
        "far_ordinance_incheon": "80%",
        "far_num": 80.0,
        "desc": "농업·임업·어업 생산 등을 위하여 관리가 필요한 지역"
    },
    "보전관리지역": {
        "bcr_national": "20% 이하",
        "bcr_national_num": 20.0,
        "bcr_ordinance_seoul": "20%",
        "bcr_ordinance_incheon": "20%",
        "bcr_num": 20.0,
        "far_national": "50% 이상 80% 이하",
        "far_national_num": 80.0,
        "far_ordinance_seoul": "80%",
        "far_ordinance_incheon": "80%",
        "far_num": 80.0,
        "desc": "자연환경보호 등을 위하여 보전이 필요하나 자연환경보전지역으로 지정하기 곤란한 지역"
    },
    "농림지역": {
        "bcr_national": "20% 이하",
        "bcr_national_num": 20.0,
        "bcr_ordinance_seoul": "20%",
        "bcr_ordinance_incheon": "20%",
        "bcr_num": 20.0,
        "far_national": "50% 이상 80% 이하",
        "far_national_num": 80.0,
        "far_ordinance_seoul": "80%",
        "far_ordinance_incheon": "80%",
        "far_num": 80.0,
        "desc": "농업진흥지역 또는 보전산지 등"
    },
    "자연환경보전지역": {
        "bcr_national": "20% 이하",
        "bcr_national_num": 20.0,
        "bcr_ordinance_seoul": "20%",
        "bcr_ordinance_incheon": "20%",
        "bcr_num": 20.0,
        "far_national": "50% 이상 80% 이하",
        "far_national_num": 80.0,
        "far_ordinance_seoul": "80%",
        "far_ordinance_incheon": "80%",
        "far_num": 80.0,
        "desc": "자연환경·수자원·생태계 보전 지역"
    }
}

class RegulationEngine:
    def __init__(self):
        pass

    def match_zoning_db(self, zoning_name: str) -> Dict[str, Any]:
        """용도지역 명칭을 표준 키와 매칭"""
        cleaned = zoning_name.replace(" ", "")
        for key in STATUTORY_LIMITS_DB:
            if key in cleaned or cleaned in key:
                return {"matched": True, "key": key, **STATUTORY_LIMITS_DB[key]}
        return {
            "matched": False,
            "key": zoning_name,
            "bcr_national": "관련 법령 확인 필요",
            "bcr_national_num": 60.0,
            "bcr_ordinance_seoul": "조례 확인 필요",
            "bcr_ordinance_incheon": "조례 확인 필요",
            "bcr_num": 50.0,
            "far_national": "관련 법령 확인 필요",
            "far_national_num": 250.0,
            "far_ordinance_seoul": "조례 확인 필요",
            "far_ordinance_incheon": "조례 확인 필요",
            "far_num": 200.0,
            "desc": "지정 용도지역 상세 확인 요망"
        }

    def analyze(self, site_info: Dict[str, Any], land_info: Dict[str, Any], ordin_bundle: Dict[str, Any],
                site_area: float = 1000.0, planned_usage: str = "공동주택 (아파트)",
                unit_count: int = 80, unit_area: float = 84.0,
                unit_breakdown: Optional[Dict[str, Any]] = None,
                is_units_undetermined: bool = False,
                cadastral_info: Optional[Dict[str, Any]] = None,
                override_far: Optional[float] = None,
                override_bcr: Optional[float] = None,
                **kwargs) -> Dict[str, Any]:
        """대지 정보, 용도지역, 계획 조건(용도/면적/타입별 세대구성)을 종합하여 건축 및 사업성 통합 분석 데이터셋 생성"""
        primary_zoning = land_info.get("primary_zoning", "제2종일반주거지역")
        db_match = self.match_zoning_db(primary_zoning)
        sido = site_info.get("sido", "서울특별시")
        sigg = site_info.get("sigg", "")

        is_seoul = "서울" in sido
        is_incheon = "인천" in sido
        is_busan = "부산" in sido
        is_gyeonggi = "경기" in sido
        sido_label = "인천시" if is_incheon else ("서울시" if is_seoul else ("경기도" if is_gyeonggi else ("부산시" if is_busan else (sido if sido else "지자체"))))

        # 1. 국토계획법 시행령상 법정 상한 (National Statutory Limits)
        national_bcr_num = float(db_match.get("bcr_national_num", 60.0))
        national_far_num = float(db_match.get("far_national_num", 250.0))
        national_bcr_str = db_match.get("bcr_national", f"{national_bcr_num:.0f}% 이하")
        national_far_str = db_match.get("far_national", f"{national_far_num:.0f}% 이하")

        # 2. 지자체 조례 및 지구단위계획 기본 상한 (Municipal Ordinance / District Plan Limits)
        if is_incheon:
            if "일반상업" in primary_zoning:
                # 인천시 도시계획조례상 일반상업지역 주거복합건축물 주거용적률 700% 제한
                bcr_ordinance_val = "70% 이하 (주거복합 60%)"
                bcr_ordinance_num = 60.0 if ("주상복합" in planned_usage or "공동주택" in planned_usage) else 70.0
                far_ordinance_val = "700% (인천시 도시계획조례 주거복합 상한 700% 제한)"
                far_ordinance_num = 700.0
            elif "중심상업" in primary_zoning:
                bcr_ordinance_val = "80% 이하 (주거복합 70%)"
                bcr_ordinance_num = 70.0 if ("주상복합" in planned_usage or "공동주택" in planned_usage) else 80.0
                far_ordinance_val = "1,000% 이하"
                far_ordinance_num = 1000.0
            elif "준주거" in primary_zoning:
                bcr_ordinance_val = "60% 이하"
                bcr_ordinance_num = 60.0
                far_ordinance_val = "300% (주상복합 300% / 상업 350%)"
                far_ordinance_num = 300.0
            else:
                bcr_ordinance_val = db_match.get("bcr_ordinance_incheon", db_match.get("bcr_ordinance_seoul", "60%"))
                bcr_ordinance_num = float(db_match.get("bcr_num", 60.0))
                far_ordinance_val = db_match.get("far_ordinance_incheon", db_match.get("far_ordinance_seoul", "250%"))
                far_ordinance_num = 250.0 if "제2종일반주거" in primary_zoning else (300.0 if "제3종일반주거" in primary_zoning else float(db_match.get("far_num", 200.0)))
        elif is_seoul:
            bcr_ordinance_val = db_match.get("bcr_ordinance_seoul", "60%")
            bcr_ordinance_num = float(db_match.get("bcr_num", 50.0))
            far_ordinance_val = db_match.get("far_ordinance_seoul", "200%")
            far_ordinance_num = float(db_match.get("far_num", 200.0))
        else:
            # 전국 범용 처리: 서울/인천 외 지역은 국토계획법을 임시 기준으로 잡고, '조례 개별 확인' 경고 텍스트 표출
            bcr_ordinance_num = float(db_match.get("bcr_national_num", 50.0))
            far_ordinance_num = float(db_match.get("far_national_num", 200.0))
            
            bcr_ordinance_val = f"⚠️ {sido_label} 조례 개별 확인 (법정 상한 {bcr_ordinance_num}% 기준 산정)"
            far_ordinance_val = f"⚠️ {sido_label} 조례 개별 확인 (법정 상한 {far_ordinance_num}% 기준 산정)"

        # 조례 본문에서 해당 용도지역 값 직접 파싱 시도
        parsed_bcr, num_bcr = self._extract_value_from_articles(ordin_bundle.get("bcr_articles", []), primary_zoning, "건폐율")
        parsed_far, num_far = self._extract_value_from_articles(ordin_bundle.get("far_articles", []), primary_zoning, "용적률")

        if parsed_bcr and num_bcr:
            bcr_ordinance_val = parsed_bcr
            bcr_ordinance_num = num_bcr
        if parsed_far and num_far:
            far_ordinance_val = parsed_far
            far_ordinance_num = num_far

        # 지자체별 상업지역 내 주거복합건축물/주상복합 특례 조례 상한 (예: 인천시 조례 일반상업 주상복합 700% 제한)
        if is_incheon and "일반상업" in primary_zoning and ("주상복합" in planned_usage or "공동주택" in planned_usage):
            far_ordinance_val = "700% (인천시 조례 주거복합 상한 700% 제한)"
            far_ordinance_num = 700.0
            bcr_ordinance_val = "60% 이하 (인천시 조례 주거복합 기준)"
            bcr_ordinance_num = 60.0

        # 3. 사용자 수동 오버라이드 (조례/지구단위계획 직접 입력 제한)
        is_far_overridden = False
        if override_far is not None and float(override_far) > 0:
            far_ordinance_num = float(override_far)
            far_ordinance_val = f"{far_ordinance_num:.0f}% (사용자/지구단위계획 직접 지정)"
            is_far_overridden = True

        is_bcr_overridden = False
        if override_bcr is not None and float(override_bcr) > 0:
            bcr_ordinance_num = float(override_bcr)
            bcr_ordinance_val = f"{bcr_ordinance_num:.0f}% (사용자/지구단위계획 직접 지정)"
            is_bcr_overridden = True

        # 4. 더 엄격한(낮은) 기준 실질 적용 (Stricter Limit Applied)
        applied_far_num = min(national_far_num, far_ordinance_num)
        applied_bcr_num = min(national_bcr_num, bcr_ordinance_num)

        applied_far_val = f"{applied_far_num:.0f}%"
        applied_bcr_val = f"{applied_bcr_num:.0f}%"

        # 5. 이중 검토 비교 요약 문구 생성
        far_comparison_summary = f"국토계획법 상한: {national_far_num:,.0f}% | {sido_label} 조례 상한: {far_ordinance_num:,.0f}% (적용: {applied_far_num:,.0f}% 제한)"
        bcr_comparison_summary = f"국토계획법 상한: {national_bcr_num:,.0f}% | {sido_label} 조례 상한: {bcr_ordinance_num:,.0f}% (적용: {applied_bcr_num:,.0f}% 제한)"

        # 대지면적 검증 정보 (토지대장 공부상 면적과 사용자 입력 면적 비교)
        area_validation = self._validate_site_area(site_area, cadastral_info)

        # 지구단위계획 / 재개발 구역 여부 종합 판별
        is_district_plan = land_info.get("is_district_plan", False)
        addr_text = site_info.get("refined_address", "")
        has_redev_keyword = any(k in addr_text for k in ["길음", "뉴타운", "재정비", "정비구역", "재개발", "재건축"])
        if any("지구단위" in z or "정비" in z or "촉진" in z for z in land_info.get("restrictions", []) + land_info.get("overlay_zones", [])):
            is_district_plan = True

        need_district_alert = is_district_plan or has_redev_keyword

        # 1. 기획설계 및 사업성 규모 산정 (Massing & Feasibility) - 엄격한 적용치 기준
        feasibility = self._calculate_massing(
            site_area, applied_bcr_num, applied_far_num, planned_usage,
            unit_count, unit_area, unit_breakdown, is_units_undetermined
        )

        # 2. 용도별 설계 제약 및 주차 산정
        design_constraints = self._analyze_design_constraints(
            planned_usage, primary_zoning, site_area, feasibility,
            unit_count, unit_area, unit_breakdown, is_units_undetermined
        )

        # 3. 최고높이 분석
        height_analysis = self._analyze_height_limits(primary_zoning, land_info, ordin_bundle.get("height_articles", []), feasibility["est_floors"])

        # 4. 4대 주요 심의 자동 판정 (O/X 및 리스크)
        deliberation_analysis = self._evaluate_deliberations(sido, sigg, primary_zoning, feasibility, planned_usage, ordin_bundle.get("deliberation_articles", []))

        # 5. 지구단위계획 및 지자체 특별 조례 & 실무 체크리스트 표 생성
        special_ordinance = self._analyze_special_ordinance(sido, sigg, is_district_plan, land_info)

        # 6. 임원진/경영진 보고용 3줄 결론 생성
        executive_summary_3lines = self._generate_executive_3lines(
            site_info, primary_zoning, applied_bcr_val, applied_far_val,
            feasibility, deliberation_analysis, need_district_alert, area_validation,
            far_summary=far_comparison_summary
        )

        return {
            "site": site_info,
            "land": land_info,
            "zoning_info": db_match,
            "area_validation": area_validation,
            "planned_conditions": {
                "site_area_sqm": site_area,
                "site_area_py": round(site_area / 3.305785, 1),
                "planned_usage": planned_usage,
                "unit_count": feasibility["effective_unit_count"],
                "unit_area": feasibility["effective_unit_area"],
                "is_undetermined": is_units_undetermined,
                "unit_breakdown": feasibility["unit_breakdown"],
                "override_far": override_far,
                "override_bcr": override_bcr
            },
            "bcr": {
                "ordinance_limit": bcr_ordinance_val,
                "ordinance_num": bcr_ordinance_num,
                "national_limit": national_bcr_str,
                "national_num": national_bcr_num,
                "applied_limit": applied_bcr_val,
                "applied_num": applied_bcr_num,
                "comparison_summary": bcr_comparison_summary,
                "is_stricter_applied": applied_bcr_num < national_bcr_num,
                "is_overridden": is_bcr_overridden,
                "law_source": f"{ordin_bundle.get('planning_ordinance', {}).get('title', f'{sido} 도시계획 조례')} 제44조 등 / 국토계획법 제77조",
                "notes": "국토계획법 법정 상한과 지자체 조례·지구단위계획 상한 중 더 엄격한(낮은) 기준이 자동 실질 적용됨"
            },
            "far": {
                "ordinance_limit": far_ordinance_val,
                "ordinance_num": far_ordinance_num,
                "national_limit": national_far_str,
                "national_num": national_far_num,
                "applied_limit": applied_far_val,
                "applied_num": applied_far_num,
                "comparison_summary": far_comparison_summary,
                "is_stricter_applied": applied_far_num < national_far_num,
                "is_overridden": is_far_overridden,
                "law_source": f"{ordin_bundle.get('planning_ordinance', {}).get('title', f'{sido} 도시계획 조례')} 제48조 등 / 국토계획법 제78조",
                "notes": "국토계획법 법정 상한과 지자체 조례·지구단위계획 상한 중 더 엄격한(낮은) 기준이 자동 실질 적용됨 (기부채납·친환경 인센티브 시 상향 가능)"
            },
            "incentives": self._get_far_incentives(primary_zoning, applied_far_num),
            "feasibility": feasibility,
            "design_constraints": design_constraints,
            "height": height_analysis,
            "deliberations": deliberation_analysis,
            "special_ordinance": special_ordinance,
            "executive_summary_3lines": executive_summary_3lines,
            "district_plan_alert": {
                "required": need_district_alert,
                "title": "지구단위계획 지침 별도 확인 필요",
                "message": (
                    "해당 대지는 지구단위계획구역 또는 정비사업(재개발·재건축·뉴타운) 구역에 해당하거나 인접해 있습니다. "
                    "「국토계획법」 제54조에 의거하여 지구단위계획구역 안에서는 본 조례 일반 기준보다 "
                    "지자체에서 고시한 **지구단위계획 결정고시 도서 및 시행지침**이 법적으로 우선 적용됩니다. "
                    "건축선 후퇴, 지정/권장 용도, 공공보행통로, 인센티브 완화 용적률 및 최고높이를 반드시 관할 지자체 도시계획과에서 별도 열람·확인하시기 바랍니다."
                )
            }
        }

    def _validate_site_area(self, input_area: float, cadastral_info: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """토지대장상 공부상 대지면적과 사용자 입력 면적 비교 검증"""
        if not cadastral_info or not cadastral_info.get("has_cadastral"):
            return {
                "has_cadastral": False,
                "is_match": True,
                "diff_sqm": 0.0,
                "diff_pct": 0.0,
                "warning": False,
                "official_area_sqm": input_area,
                "official_area_py": round(input_area / 3.305785, 1)
            }

        official_area = cadastral_info.get("official_area_sqm", 0.0)
        diff_sqm = abs(input_area - official_area)
        diff_pct = (diff_sqm / official_area * 100.0) if official_area > 0 else 0.0
        warning = diff_sqm > 1.0  # 1m2 이상 차이 시 경고

        return {
            "has_cadastral": True,
            "official_area_sqm": official_area,
            "official_area_py": cadastral_info.get("official_area_py", round(official_area / 3.305785, 1)),
            "input_area_sqm": input_area,
            "diff_sqm": round(diff_sqm, 2),
            "diff_pct": round(diff_pct, 1),
            "is_match": not warning,
            "warning": warning,
            "jimok": cadastral_info.get("jimok", "대"),
            "official_price": cadastral_info.get("official_price", "미공시"),
            "road_side": cadastral_info.get("road_side", "중로각지"),
            "topography_height": cadastral_info.get("topography_height", "평지")
        }

    def _calculate_massing(self, site_area: float, bcr_pct: float, far_pct: float, usage: str,
                           unit_count: int, unit_area: float,
                           unit_breakdown: Optional[Dict[str, Any]], is_undetermined: bool) -> Dict[str, Any]:
        """기획설계 건축 규모 및 연면적/층수/주차 개략 산정 (미정 옵션 및 복합구성 완벽 대응)"""
        max_building_area = site_area * (bcr_pct / 100.0)
        max_ground_gfa = site_area * (far_pct / 100.0)

        # 인센티브 완화 적용 시 예상 용적률 (통상 1.15~1.2배 또는 법정상한)
        incentive_far_pct = min(far_pct * 1.20, far_pct + 50.0)
        incentive_ground_gfa = site_area * (incentive_far_pct / 100.0)

        # 기준 층고
        if "공동주택" in usage:
            floor_height = 3.0
            typical_coverage_use = 0.55  # 기준층 건폐율 실사용률
        elif "오피스텔" in usage:
            floor_height = 3.3
            typical_coverage_use = 0.65
        else:
            floor_height = 3.8
            typical_coverage_use = 0.70

        typical_floor_area = max_building_area * typical_coverage_use
        if typical_floor_area <= 0:
            typical_floor_area = 100.0

        est_floors = max(1, int(round(max_ground_gfa / typical_floor_area)))
        if "주거" in usage and est_floors > 35:
            est_floors = 35
        est_height = round(est_floors * floor_height, 1)

        # 지하 연면적 산정 (지상 연면적의 약 45% 추정: 주차장, 기계전기실)
        est_basement_gfa = max_ground_gfa * 0.45
        est_total_gfa = max_ground_gfa + est_basement_gfa

        # 세대 구성 산정
        effective_breakdown = {}
        effective_unit_count = unit_count
        effective_unit_area = unit_area
        effective_apt_count = 0
        effective_off_count = 0

        if is_undetermined:
            # 💡 [세대 구성 미정 옵션]: 법정 최대 용적률 기반 시장 표준 비율 자동 추정
            if "주상복합" in usage:
                # 비주거 10% 제외, 주거 70% (84타입 60%, 59타입 40%), 오피스텔 20% (59타입 50%, 29타입 50%)
                apt_net = max_ground_gfa * 0.70 * 0.75
                off_net = max_ground_gfa * 0.20 * 0.50
                u84 = max(1, int(round((apt_net * 0.60) / 84.0)))
                u59 = max(1, int(round((apt_net * 0.40) / 59.0)))
                off59 = max(1, int(round((off_net * 0.50) / 59.0)))
                off29 = max(1, int(round((off_net * 0.50) / 29.0)))
                effective_breakdown = {
                    "apt": {"84": u84, "59": u59, "74": 0, "104": 0},
                    "officetel": {"59": off59, "29": off29, "39": 0, "84": 0}
                }
                effective_apt_count = u84 + u59
                effective_off_count = off59 + off29
                effective_unit_count = effective_apt_count + effective_off_count
                effective_unit_area = round((apt_net + off_net) / effective_unit_count, 1) if effective_unit_count > 0 else 84.0

            elif "공동주택" in usage:
                # 전용률 75% 적용, 국민평형 84타입 60%, 59타입 40%
                apt_net = max_ground_gfa * 0.75
                u84 = max(1, int(round((apt_net * 0.60) / 84.0)))
                u59 = max(1, int(round((apt_net * 0.40) / 59.0)))
                effective_breakdown = {
                    "apt": {"84": u84, "59": u59, "74": 0, "104": 0},
                    "officetel": {}
                }
                effective_apt_count = u84 + u59
                effective_unit_count = effective_apt_count
                effective_unit_area = round(apt_net / effective_unit_count, 1) if effective_unit_count > 0 else 84.0

            elif "오피스텔" in usage:
                # 전용률 50% 적용, 59타입 50%, 29타입 50%
                off_net = max_ground_gfa * 0.50
                off59 = max(1, int(round((off_net * 0.50) / 59.0)))
                off29 = max(1, int(round((off_net * 0.50) / 29.0)))
                effective_breakdown = {
                    "apt": {},
                    "officetel": {"59": off59, "29": off29, "39": 0, "84": 0}
                }
                effective_off_count = off59 + off29
                effective_unit_count = effective_off_count
                effective_unit_area = round(off_net / effective_unit_count, 1) if effective_unit_count > 0 else 45.0
            else:
                effective_unit_count = unit_count
                effective_unit_area = unit_area
        else:
            # 사용자가 입력한 세대 구성 파싱
            if unit_breakdown:
                effective_breakdown = unit_breakdown
                apt_dict = unit_breakdown.get("apt", {})
                off_dict = unit_breakdown.get("officetel", {})
                effective_apt_count = sum(apt_dict.values())
                effective_off_count = sum(off_dict.values())
                effective_unit_count = effective_apt_count + effective_off_count
                if effective_unit_count <= 0:
                    effective_unit_count = unit_count
                
                # 타입별 전용면적 가중평균 산정
                total_net = 0.0
                for k, v in apt_dict.items():
                    try:
                        total_net += float(k) * v
                    except (ValueError, TypeError):
                        total_net += 84.0 * v
                for k, v in off_dict.items():
                    try:
                        total_net += float(k) * v
                    except (ValueError, TypeError):
                        total_net += 45.0 * v
                if effective_unit_count > 0 and total_net > 0:
                    effective_unit_area = round(total_net / effective_unit_count, 1)
                else:
                    effective_unit_area = unit_area
            else:
                effective_unit_count = unit_count
                effective_unit_area = unit_area

        return {
            "max_building_area_sqm": round(max_building_area, 1),
            "max_building_area_py": round(max_building_area / 3.305785, 1),
            "max_ground_gfa_sqm": round(max_ground_gfa, 1),
            "max_ground_gfa_py": round(max_ground_gfa / 3.305785, 1),
            "incentive_far_pct": round(incentive_far_pct, 1),
            "incentive_ground_gfa_sqm": round(incentive_ground_gfa, 1),
            "incentive_ground_gfa_py": round(incentive_ground_gfa / 3.305785, 1),
            "est_floors": est_floors,
            "est_height_m": est_height,
            "floor_height_m": floor_height,
            "est_basement_gfa_sqm": round(est_basement_gfa, 1),
            "est_total_gfa_sqm": round(est_total_gfa, 1),
            "est_total_gfa_py": round(est_total_gfa / 3.305785, 1),
            "is_undetermined": is_undetermined,
            "unit_breakdown": effective_breakdown,
            "effective_unit_count": effective_unit_count,
            "effective_unit_area": effective_unit_area,
            "effective_apt_count": effective_apt_count,
            "effective_off_count": effective_off_count
        }

    def _analyze_design_constraints(self, usage: str, zoning: str, site_area: float, feasibility: Dict[str, Any],
                                    unit_count: int, unit_area: float,
                                    unit_breakdown: Optional[Dict[str, Any]], is_undetermined: bool) -> Dict[str, Any]:
        """용도별 필수 설계 기준, 사선제한, 주차대수 산정 (타입별 세대수 완벽 반영)"""
        is_commercial = "상업" in zoning
        is_residential = "주거" in zoning

        # 1. 주거 / 비주거 비율 및 용도별 제한
        usage_rules = []
        if "주상복합" in usage:
            if is_commercial:
                usage_rules.append("비주거시설 의무비율: 지상 연면적의 10% 이상 상업/업무시설 필수 확보 (지자체 도시계획조례)")
                usage_rules.append("주거부문과 비주거(상가/오피스텔) 부문의 동선 및 주차구역 완전 분리 계획 필요")
            else:
                usage_rules.append("준주거지역 내 주거복합 건축 시 비주거비율 충족에 따른 용적률 인센티브 확인 요망")
        elif "오피스텔" in usage:
            usage_rules.append("오피스텔 건축기준(국토부 고시): 발코니 설치 불가, 전용 120㎡ 이하 바닥난방 설치 허용")
            usage_rules.append("피난계단 2개소 이상 설치 및 직통계단 보행거리 30m 이하(내화구조 50m 이하) 준수")
        elif "공동주택" in usage:
            usage_rules.append("부대복리시설 기준: 50세대 이상 어린이놀이터, 100세대 이상 경로당, 300세대 이상 어린이집 의무화")
            usage_rules.append("동간거리 규정: 채광방향 이격거리 및 인접대지경계선 이격거리(0.5H 이상) 준수")

        # 2. 사선제한 및 대지 안의 공지
        setback_rules = [
            {
                "item": "정북방향 일조권 사선제한 (건축법 제61조)",
                "status": "적용 (필수)" if is_residential else "적용 제외 (상업지역 면제)",
                "details": "전용·일반주거지역 건축 시 정북방향 대지경계선으로부터 높이 10m 이하는 1.5m, 10m 초과는 높이의 1/2 이상 이격 필수" if is_residential else "상업지역은 일조권 사선제한 미적용(단, 공동주택 채광방향 이격 검토 필요)"
            },
            {
                "item": "대지 안의 공지 (건축선 이격)",
                "status": "의무 이격 (1.0m ~ 3.0m)",
                "details": f"{usage} 기준: 건축선으로부터 1.5m~3.0m 이격, 보행공간 및 식재구역 확보 (지자체 건축조례 별표)"
            },
            {
                "item": "대지 안의 공지 (인접대지경계선 이격)",
                "status": "의무 이격 (0.5m ~ 2.0m)",
                "details": "인접대지경계선으로부터 1.0m~2.0m 이상 이격하여 통풍 및 채광 확보"
            }
        ]

        # 3. 주차대수 산정 (타입별 세대수 및 전용면적 정밀 반영)
        eff_count = feasibility["effective_unit_count"]
        breakdown = feasibility["unit_breakdown"]

        legal_parking = 0
        ordinance_parking = 0
        recommended_parking = 0
        basis_parts = []

        if breakdown and (breakdown.get("apt") or breakdown.get("officetel")):
            # 타입별 정밀 산정
            apt_dict = breakdown.get("apt", {})
            off_dict = breakdown.get("officetel", {})

            apt_parking_legal = 0
            for type_name, count in apt_dict.items():
                if count <= 0: continue
                try:
                    type_area = float(type_name)
                except (ValueError, TypeError):
                    type_area = 84.0
                ratio = 1.3 if type_area > 85.0 else (1.0 if type_area >= 60.0 else 0.7)
                apt_parking_legal += math.ceil(count * ratio)

            off_parking_legal = 0
            for type_name, count in off_dict.items():
                if count <= 0: continue
                try:
                    type_area = float(type_name)
                except (ValueError, TypeError):
                    type_area = 59.0
                ratio = 1.0 if type_area >= 60.0 else (0.7 if type_area >= 30.0 else 0.5)
                off_parking_legal += math.ceil(count * ratio)

            # 비주거 상가 주차
            com_area = feasibility["max_ground_gfa_sqm"] * (0.10 if "주상복합" in usage else 0.0)
            com_parking = math.ceil(com_area / 134.0) if com_area > 0 else 0

            legal_parking = int(apt_parking_legal + off_parking_legal + com_parking)
            ordinance_parking = int(math.ceil(legal_parking * 1.15))
            recommended_parking = int(math.ceil(legal_parking * 1.30))

            if apt_parking_legal > 0:
                basis_parts.append(f"공동주택 {sum(apt_dict.values())}세대({apt_parking_legal}대)")
            if off_parking_legal > 0:
                basis_parts.append(f"오피스텔 {sum(off_dict.values())}호({off_parking_legal}대)")
            if com_parking > 0:
                basis_parts.append(f"비주거 상가({com_parking}대)")
            basis = " + ".join(basis_parts) + f" (법정합계: {legal_parking}대)"
        else:
            # 단일 면적 입력 산정
            if "공동주택" in usage:
                ratio = 1.0 if unit_area <= 85 else 1.3
                legal_parking = int(math.ceil(eff_count * ratio))
                ordinance_parking = int(math.ceil(eff_count * 1.15))
                recommended_parking = int(math.ceil(eff_count * 1.30))
                basis = f"세대당 {ratio}대 (전용 {unit_area}㎡ 기준) / 지자체 조례 세대당 1.1대 이상 강화"
            elif "오피스텔" in usage:
                legal_parking = int(math.ceil(eff_count * 1.0))
                ordinance_parking = int(math.ceil(eff_count * 1.0))
                recommended_parking = int(math.ceil(eff_count * 1.15))
                basis = "호실당 1.0대 의무 (주차장법 시행령 별표 1)"
            elif "주상복합" in usage:
                res_parking = int(math.ceil(eff_count * 1.0))
                com_area = feasibility["max_ground_gfa_sqm"] * 0.15
                com_parking = int(math.ceil(com_area / 134.0))
                legal_parking = res_parking + com_parking
                ordinance_parking = int(math.ceil(legal_parking * 1.15))
                recommended_parking = int(math.ceil(legal_parking * 1.30))
                basis = f"주거 세대당 1.0대({res_parking}대) + 비주거 134㎡당 1대({com_parking}대) 복합산정"
            else:
                gfa = feasibility["max_ground_gfa_sqm"]
                legal_parking = int(math.ceil(gfa / 150.0))
                ordinance_parking = int(math.ceil(gfa / 134.0))
                recommended_parking = int(math.ceil(gfa / 100.0))
                basis = "시설면적 134㎡~150㎡ 당 1대 산정"

        return {
            "usage_rules": usage_rules,
            "setback_rules": setback_rules,
            "parking": {
                "legal_count": max(1, legal_parking),
                "ordinance_count": max(1, ordinance_parking),
                "recommended_count": max(1, recommended_parking),
                "basis": basis,
                "ev_charging_count": max(1, int(math.ceil(recommended_parking * 0.05))),  # 친환경자동차법 5% 의무
                "accessibility_count": max(1, int(math.ceil(recommended_parking * 0.03)))  # 장애인전용 2~4%
            }
        }

    def _analyze_height_limits(self, zoning: str, land_info: Dict[str, Any], height_articles: List[Dict[str, Any]], est_floors: int) -> Dict[str, Any]:
        """건축법 및 조례에 따른 최고높이 및 층수 한도 분석"""
        is_residential = any(k in zoning for k in ["전용주거", "일반주거"])
        is_1st_exclusive = "제1종전용주거" in zoning
        is_1st_general = "제1종일반주거" in zoning

        base_rules = [
            {
                "category": "가로구역별 건축물 최고높이 (건축법 제60조)",
                "limit": "지자체 고시 최고높이 구역 확인 필수",
                "tag": "주의",
                "details": "허가권자가 도로 너비, 경관 등을 감안하여 가로구역별 최고높이를 고시한 경우 고시 기준 최우선 준수"
            },
            {
                "category": "일조 등의 확보를 위한 높이제한 (건축법 제61조)",
                "limit": "정북방향 대지경계선 이격거리 준수",
                "tag": "규제" if is_residential else "정상",
                "details": (
                    "• 높이 10m 이하 부분: 정북방향 경계선으로부터 1.5m 이상 이격\n"
                    "• 높이 10m 초과 부분: 해당 부분 높이의 1/2 이상 이격 (사선 경사 셋백 필수)"
                ) if is_residential else "상업지역은 정북 일조권 사선제한 미적용"
            }
        ]

        if is_1st_general:
            base_rules.append({
                "category": "제1종일반주거지역 층수제한 (국토계획법)",
                "limit": "4층 이하 제한 (필로티 주차장 시 5층 가능)",
                "tag": "규제",
                "details": "저층주택 중심 지역으로 건축물 층수 4개 층 이하로 엄격 제한"
            })
        elif is_1st_exclusive:
            base_rules.append({
                "category": "제1종전용주거지역 높이제한 (조례)",
                "limit": "2층 이하로서 8m 이하",
                "tag": "규제",
                "details": "주거용 2층 이하 / 8m 이하 (지붕 경사 3:10 이상 시 최대 12m)"
            })

        # 고도지구 체크
        overlay_zones = land_info.get("overlay_zones", [])
        is_altitude_district = any("고도" in z for z in overlay_zones)
        if is_altitude_district:
            base_rules.insert(0, {
                "category": "고도지구 제한 (도시관리계획)",
                "limit": "고도지구 결정고시 절대높이 준수",
                "tag": "규제",
                "details": "도시관리계획으로 결정된 절대 최고높이(해발 또는 지표면 기준) 초과 불가"
            })

        summary_txt = f"예상 계획규모 지상 {est_floors}층 (약 {round(est_floors * 3.1, 1)}m) / 가로구역 고시 및 일조사선 동시 적용"
        return {
            "summary_limit": summary_txt,
            "est_floors": est_floors,
            "rules": base_rules
        }

    def _evaluate_deliberations(self, sido: str, sigg: str, zoning: str, feasibility: Dict[str, Any], usage: str, delib_articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """4대 심의(건축/소방/교통/경관) O/X 자동 판정 및 리스크 평가"""
        gfa = feasibility["est_total_gfa_sqm"]
        floors = feasibility["est_floors"]
        height = feasibility["est_height_m"]

        # 1. 건축심의 판정
        is_metro_arch = (floors >= 21 or gfa >= 100000)
        is_local_arch = (gfa >= 3000 or "공동주택" in usage or "오피스텔" in usage)
        arch_required = is_metro_arch or is_local_arch
        arch_level = "시(광역) 건축심의 [심의/규제]" if is_metro_arch else ("구(기초) 건축심의 [심의/규제]" if is_local_arch else "심의 제외 [정상]")
        arch_tag = "규제" if arch_required else "정상"

        # 2. 소방 심의 / 소방동의 판정
        is_fire_consent = (gfa >= 400)
        is_fire_performance = (floors >= 30 or height >= 100 or gfa >= 200000)
        fire_required = is_fire_performance or is_fire_consent
        if is_fire_performance:
            fire_level = "소방 성능위주설계 심의 대상 [심의/규제]"
            fire_tag = "규제"
        elif is_fire_consent:
            fire_level = "건축허가 소방동의 대상 [주의]"
            fire_tag = "주의"
        else:
            fire_level = "소방동의 경미 대상 [정상]"
            fire_tag = "정상"

        # 3. 교통영향평가 판정
        if "공동주택" in usage or "주상복합" in usage:
            traffic_required = (gfa >= 20000)
        elif "오피스텔" in usage or "업무" in usage:
            traffic_required = (gfa >= 25000)
        else:
            traffic_required = (gfa >= 12000)
        traffic_tag = "규제" if traffic_required else "정상"

        # 4. 경관심의 판정
        landscape_required = (floors >= 7 or gfa >= 3000)
        landscape_tag = "규제" if landscape_required else "정상"

        risk_count = sum(1 for t in [arch_tag, fire_tag, traffic_tag, landscape_tag] if t == "규제")

        return {
            "risk_summary": {
                "high_risk_count": risk_count,
                "overall_grade": "심의 리스크 높음 (2~4대 심의 수반)" if risk_count >= 2 else ("보통 (1~2개 심의 대응)" if risk_count == 1 else "낮음 (경미 인허가)"),
                "total_timeline_est": "약 3.0 ~ 4.5개월 (심의 통합 접수 시 3개월 내외)" if risk_count >= 2 else "약 1.5 ~ 2.0개월"
            },
            "items": [
                {
                    "name": "건축위원회 심의",
                    "required": "O (대상)" if arch_required else "X (비대상)",
                    "tag": arch_tag,
                    "target_detail": arch_level,
                    "timeline": "약 1.5 ~ 2.5개월",
                    "docs": "건축계획서, 배치도, 평면·입면·단면도, 구조계획서, 경관계획서",
                    "checkpoints": "공개공지 배치 적정성, 입면 차폐도, 보행축 연결, 굴토심의(지하2층 이상 흙막이 안정성) 병행 여부",
                    "authority": f"{sido} 및 {sigg} 건축위원회",
                    "law": "건축법 제4조 및 영 제5조의5"
                },
                {
                    "name": "소방 성능위주설계 / 소방동의",
                    "required": "O (대상)" if fire_required else "X (비대상)",
                    "tag": fire_tag,
                    "target_detail": fire_level,
                    "timeline": "약 2.0 ~ 3.0개월 (성능위주설계 시) / 허가 처리 시 14일 (소방동의)",
                    "docs": "소방시설 설계도서, 피난안전구역 계획서, 화재 및 피난 시뮬레이션 보고서",
                    "checkpoints": "비상용 승강기(31m 초과), 소방관 진입창(11층 이하), 특별피난계단 제연설비, 피난대피공간 적정성",
                    "authority": f"관할 소방서 및 {sido} 소방재난본부",
                    "law": "소방시설법 제6조 및 영 제11조"
                },
                {
                    "name": "교통영향평가 (교통심의)",
                    "required": "O (대상)" if traffic_required else "X (비대상)",
                    "tag": traffic_tag,
                    "target_detail": f"연면적 기준 {'충족 (심의 대상)' if traffic_required else '미달 (심의 제외)'}",
                    "timeline": "약 2.0 ~ 3.5개월",
                    "docs": "교통영향평가 보고서, 교차로 서비스수준 분석서, 진출입 동선 계획",
                    "checkpoints": "단지 진출입구 가·감속 차로 확보, 주변 가로 교통체증 영향, 법정 주차 120% 이상 확보 권고 대응",
                    "authority": f"{sido} 교통영향평가 심의위원회",
                    "law": "도시교통정비 촉진법 제15조"
                },
                {
                    "name": "경관심의 (경관위원회)",
                    "required": "O (대상)" if landscape_required else "X (비대상)",
                    "tag": landscape_tag,
                    "target_detail": f"규모/구역 기준 {'충족 (심의 대상)' if landscape_required else '미달 (심의 제외)'}",
                    "timeline": "약 1.0 ~ 2.0개월 (건축심의와 공동위원회 가능)",
                    "docs": "경관계획서, 조망점별 시뮬레이션(경관 시곡면), 색채 및 야간경관 조명계획서",
                    "checkpoints": "스카이라인 조화, 통경축(바람길) 확보, 외벽 주조색·보조색 비율(서울시 색채기준 등)",
                    "authority": f"{sido} 및 {sigg} 경관위원회",
                    "law": "경관법 제26조~제28조"
                }
            ],
            "fire_safety_notes": [
                "🚒 **소방관 진입창 (건축물 방화구조규칙 제18조의2)**: 2층 이상 11층 이하 층별 도로면 방향 90cm×120cm 이상 붉은색 역삼각형 표식 진입창 필수 설치",
                "🚪 **아파트 대피공간/하향식 피난구 (건축법 시행령 제46조)**: 4층 이상 세대 발코니에 2㎡ 이상 대피공간 또는 인접세대 경량칸막이·하향식 사다리 설치",
                "🛗 **비상용 승강기 (건축법 제64조)**: 건축물 높이 31m 초과 시 비상용 승강기 의무 설치 (정전 시 60초 이내 예비전원 전환)",
                "🔥 **지하주차장 스프링클러 및 방화구획**: 최근 전기차 화재 대응 기준 강화에 따라 습식 스프링클러 헤드 간격 2.3m 이하 및 방화셔터 연동 강화"
            ]
        }

    def _get_far_incentives(self, zoning: str, base_far: float) -> List[Dict[str, str]]:
        """용적률 완화 및 인센티브 가능 항목 도출"""
        return [
            {
                "item": "공공기여 (토지·시설 기부채납)",
                "target": "용적률 최대 120%~130% 완화",
                "condition": "공공청사, 도서관, 공공보행통로, 도로 확장 등 부지 또는 시설물 기부채납 시 제공 비율에 비례 산정"
            },
            {
                "item": "공공임대주택 추가 건립 (국토계획법 제78조)",
                "target": "법적 상한 용적률까지 완화",
                "condition": "조례 용적률 초과분의 50%를 공공임대주택으로 공급 시 해당 용도지역의 법정 상한까지 허용"
            },
            {
                "item": "친환경 ZEB(제로에너지건축물) 및 녹색건축 인증",
                "target": "용적률 및 최고높이 최대 15% 완화",
                "condition": "녹색건축인증 우수 이상 + ZEB 1~5등급 취득 시 인증 등급에 따라 11%~15% 차등 완화"
            },
            {
                "item": "지능형건축물 (IBS) 인증",
                "target": "용적률 및 최고높이 최대 15% 완화",
                "condition": "건축물 자동화, 정보통신 등 지능형건축물 인증 1~4등급 취득 시 등급별 완화 적용"
            },
            {
                "item": "공개공지 확보 (건축법 제43조)",
                "target": "용적률 및 높이 기준 1.2배 이하 완화",
                "condition": "일반주거·상업·준공업지역에서 대지면적의 5~10% 이상 상시 개방 쉼터/소공원 제공 시"
            }
        ]

    def _analyze_special_ordinance(self, sido: str, sigg: str, is_district_plan: bool, land_info: Dict[str, Any]) -> Dict[str, Any]:
        """지자체별 특화 조례 및 지구단위계획 실무 체크리스트 표 생성"""
        special_highlights = []
        if "서울" in sido:
            special_highlights.append("🏙️ **서울시 2040 도시기본계획 & 높이규제 완화**: 일률적 35층 높이 제한 폐지, 스카이라인 유연화 적용 (단, 가로구역 및 일조권 규정은 유지)")
            special_highlights.append("🌱 **서울시 녹색건축물 설계기준**: 연면적 500㎡ 이상 신축 시 신재생에너지 설치 의무비율(12% 이상) 및 에너지효율 1++등급 준수")
            special_highlights.append("🚗 **서울시 부설주차장 조례**: 도심지(상업지역) 주차상한제 적용 구역 여부 확인 (과다 주차 설치 제한)")
        elif "경기" in sido:
            special_highlights.append("🏘️ **경기도 시·군별 도시계획조례 편차**: 성남·수원·용인 등 시군별로 비주거 의무비율 및 개발행위허가 경사도 기준(15~20도 이하) 상이하므로 해당 시 조례 필수 검토")
            special_highlights.append("🅿️ **주차장 설치 조례 강화**: 수도권 신도시 구역의 경우 세대당 1.2~1.3대 이상 지자체 심의 권고사항 빈번")
        elif "부산" in sido:
            special_highlights.append("🌊 **부산시 해안경관 관리계획**: 해운대·광안리 등 수변지역 해안선 이격거리 및 통경축 확보 의무화")
            special_highlights.append("🏢 **상업지역 주거용적률 차등제**: 상업지역 내 주거복합 건축물 주거비율에 따른 용적률 슬라이딩 하향 규정 검토 필요")
        else:
            special_highlights.append("📌 **관할 지자체 건축조례 별표**: 대지 안의 공지(건축선/인접대지경계선 이격) 및 일조권 정북방향 이격 세부 기준 확인 요망")

        # 📋 지구단위계획 상세 지침 실무 체크리스트 표 (상세 6개 항목)
        checklist_table = [
            {
                "카테고리": "1. 건축선 후퇴 및 전면공지",
                "세부 규정 항목": "도로변 건축한계선(1.5m~3.0m)",
                "법적 및 지침 기준": "보도형 전면공지 조성 (차도/보도 단차 및 화단·계단 등 통행장애물 설치 금지, 투수블록 포장)",
                "실무 설계 점검사항": "지상 1층 기둥 돌출 불가, 켄틸레버(처마) 1m 이내 제한, 지하층 환기구(D/A) 지상 노출 배제",
                "완화 및 인센티브": "전면공지 유효폭 2m 이상 확보 시 대지안의공지 완화 인정"
            },
            {
                "카테고리": "2. 지정·권장 및 불허용도",
                "세부 규정 항목": "정주환경 저해 시설 입점 제한",
                "법적 및 지침 기준": "권장: 주거, 판매, 근생, 업무 / 불허: 위락시설(유흥·단란주점), 숙박시설, 안마시술소, 위험물저장시설, 장례식장",
                "실무 설계 점검사항": "지하 1층 및 지상 1~2층 상가 임대MD 계획 시 불허용도 업종 원천 배제 확인",
                "완화 및 인센티브": "권장용도 50% 이상 계획 시 용적률 1.1배 인센티브 적용"
            },
            {
                "카테고리": "3. 공공보행통로 의무 설치",
                "세부 규정 항목": "대지 관통 통로 (폭 4.0m~6.0m)",
                "법적 및 지침 기준": "24시간 일반 대중에게 상시 무상 개방, 통로 내 담장·폐쇄형 게이트 설치 불가, 지적상 분할 불가",
                "실무 설계 점검사항": "인접 단지 보행축과 선형 일치 필수, 상공 필로티 관통 시 유효 천장고 4.5m 이상 확보",
                "완화 및 인센티브": "보행통로 부지 면적에 비례하여 기준용적률의 최대 1.15배 가산"
            },
            {
                "카테고리": "4. 인센티브 완화 용적률",
                "세부 규정 항목": "기준 ➔ 허용 ➔ 상한 용적률 체계",
                "법적 및 지침 기준": "허용: ZEB인증(최대 +15%), 공개공지 초과확보(+10%) / 상한: 공공시설(도로, 공원, 어린이집) 기부채납 가중치 산식",
                "실무 설계 점검사항": "기부채납 제공 면적 가액 산정 및 지자체 도시관리계획 사전협상 마일스톤 확정",
                "완화 및 인센티브": "해당 용도지역 법정 상한 용적률 범위 내 최대치 수령 가능"
            },
            {
                "카테고리": "5. 최고높이 및 층수 규정",
                "세부 규정 항목": "지구단위계획 지정 최고높이",
                "법적 및 지침 기준": "지침상 지정 최고높이(예: 35m 이하 또는 12층 이하, 중심상업지구 100m 이하 등) 절대 준수",
                "실무 설계 점검사항": "옥탑 권상기실 수평투영면적이 건축면적 1/8 초과 시 층수 산입 주의, 옥상 조경 및 쿨루프 의무",
                "완화 및 인센티브": "우수디자인 공동주택 선정 시 최고높이 1.1~1.2배 완화 검토"
            },
            {
                "카테고리": "6. 외관 및 1층 가로활성화",
                "세부 규정 항목": "가로활성화 투시벽면율 50%",
                "법적 및 지침 기준": "전면도로 접한 1층 외벽면의 50% 이상을 투시형 유리벽(쇼윈도)으로 계획, 셔터 설치 지양",
                "실무 설계 점검사항": "단지 외벽 연속 길이 40m 초과 시 입면 분절(Mass 분할) 및 통경축(바람길) 확보",
                "완화 및 인센티브": "가로활성화 디자인 반영 시 건축위원회 심의 통과 용이"
            }
        ]

        return {
            "special_highlights": special_highlights,
            "district_plan_checklist": checklist_table
        }

    def _generate_executive_3lines(self, site_info: Dict[str, Any], zoning: str, bcr_val: str, far_val: str,
                                   feasibility: Dict[str, Any], delibs: Dict[str, Any], is_alert: bool,
                                   area_validation: Dict[str, Any],
                                   far_summary: Optional[str] = None) -> List[str]:
        """임원진/경영진 보고용 3줄 요약 결론"""
        floors = feasibility["est_floors"]
        gfa_py = feasibility["max_ground_gfa_py"]
        risk_count = delibs["risk_summary"]["high_risk_count"]
        timeline = delibs["risk_summary"]["total_timeline_est"]
        eff_units = feasibility["effective_unit_count"]

        # Line 1: 개발 규모 및 면적 정합성
        area_note = f" (공부상 대지면적 {area_validation['official_area_sqm']:,.0f}㎡ 대비 입력 검토)" if area_validation.get("has_cadastral") else ""
        far_tag = f"[{far_summary}] 적용" if far_summary else f"적용 건폐율 {bcr_val}, 용적률 {far_val}"
        line1 = f"1️⃣ [개발 규모]: 본 대지는 「{zoning}」으로 {far_tag} 기준 지상연면적 약 {gfa_py:,.0f}평(최고 {floors}층, 총 {eff_units}세대/호 규모) 개발이 가능하며, 친환경(ZEB)·기부채납 인센티브 적용 시 최대 {feasibility['incentive_far_pct']}%까지 용적률 상향이 가능합니다.{area_note}"

        # Line 2: 심의 리스크
        line2 = f"2️⃣ [심의 리스크]: 사업 추진 시 총 {risk_count}대 핵심 심의(건축심의, 소방동의/성능위주, 경관심의 등) 대상에 해당하여 착공 전 사전 인허가 소요 기간 {timeline}을 설계 마일스톤에 필수 반영해야 합니다."

        # Line 3: 핵심 선결과제
        if is_alert:
            line3 = "3️⃣ [핵심 선결과제]: 지구단위계획 수립 구역이므로 관할 구청 도시계획과 지침상 1.5m~3.0m 전면공지 건축한계선 후퇴 및 불허용도(위락·숙박 배제) 충족 여부를 기획설계 배치도에 우선 반영해야 합니다."
        else:
            line3 = "3️⃣ [핵심 선결과제]: 정북방향 일조사선제한(10m 초과 1/2 셋백)에 따른 북측 계단식 매싱 최적화 및 법정 주차대수 확보가 기획설계의 핵심 성공 요인입니다."

        return [line1, line2, line3]

    def _extract_value_from_articles(self, articles: List[Dict[str, Any]], zoning: str, target_type: str) -> Tuple[Optional[str], Optional[float]]:
        """조문 텍스트에서 '제3종일반주거지역: 50퍼센트' 형태의 패턴 정규식 추출"""
        z_core = zoning.replace(" ", "")
        
        primary_title_pattern = f"용도지역안에서의{target_type}"
        sorted_articles = sorted(
            articles,
            key=lambda a: 0 if primary_title_pattern in a.get("title", "").replace(" ", "") else 1
        )

        for a in sorted_articles:
            title = a.get("title", "").replace(" ", "")
            if "완화" in title and primary_title_pattern not in title:
                continue

            content = a.get("content", "")
            lines = content.split("\n")
            for line in lines:
                clean_line = line.replace(" ", "")
                if z_core in clean_line and "퍼센트" in clean_line:
                    m = re.search(r"(\d+(?:천)?(?:\.\d+)?)\s*퍼센트", line)
                    if m:
                        val = m.group(1)
                        if val == "1천":
                            num_val = 1000.0
                            val_str = "1,000"
                        else:
                            num_val = float(val)
                            val_str = val
                        return f"{val_str}% 이하", num_val
        return None, None
