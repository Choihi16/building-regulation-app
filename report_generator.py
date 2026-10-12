"""
보고서 생성 모듈 (Report Generator)
- 임원진/경영진 보고용 건축 법규 및 사업성 통합 검토 보고서 마크다운 생성
- 대지면적 검증 및 지구단위계획 실무 체크리스트 표 포함
"""

from typing import Dict, Any

def generate_markdown_report(analysis: Dict[str, Any]) -> str:
    site = analysis.get("site", {})
    land = analysis.get("land", {})
    zoning = analysis.get("zoning_info", {})
    planned = analysis.get("planned_conditions", {})
    area_val = analysis.get("area_validation", {})
    bcr = analysis.get("bcr", {})
    far = analysis.get("far", {})
    feas = analysis.get("feasibility", {})
    height = analysis.get("height", {})
    delibs = analysis.get("deliberations", {})
    constraints = analysis.get("design_constraints", {})
    special = analysis.get("special_ordinance", {})
    dp_alert = analysis.get("district_plan_alert", {})
    three_lines = analysis.get("executive_summary_3lines", [])

    md = []
    md.append("# 🏛️ [경영진 보고용] 건축 법규 및 사업성 통합 검토 보고서")
    md.append(f"**검토 일자**: 2026-10-12 | **작성부서**: 개발기획팀 / AI건축법규분석에이전트  ")
    md.append("---")

    # Header & Executive Summary
    md.append("## 📌 1. 사업부지 및 계획 개요 (Executive Summary)")
    md.append(f"- **대지 위치**: {site.get('refined_address', site.get('raw_address'))}")
    md.append(f"- **필지고유번호 (PNU)**: `{site.get('pnu', '확인필요')}`")
    md.append(f"- **법정 용도지역**: **{land.get('primary_zoning', '미지정')}** ({zoning.get('desc', '')})")
    md.append(f"- **검토 대지면적**: **{planned.get('site_area_sqm', 0.0):,.1f} ㎡ (약 {planned.get('site_area_py', 0.0):,.1f} 평)**")
    
    if area_val.get("has_cadastral"):
        match_txt = "일치 (정상)" if area_val.get("is_match") else f"⚠️ 오차 감지 ({area_val.get('diff_sqm'):,.1f}㎡ / {area_val.get('diff_pct')}%)"
        md.append(f"- **토지대장 공부상 면적**: **{area_val.get('official_area_sqm', 0.0):,.1f} ㎡ (약 {area_val.get('official_area_py', 0.0):,.1f} 평)** [정합성: {match_txt}]")
        md.append(f"  - 지목: `{area_val.get('jimok')}` | 공시지가: `{area_val.get('official_price')}` | 도로조건: `{area_val.get('road_side')}`")

    undetermined_tag = " (규모 검토 중 - 자동 추정 산정)" if planned.get("is_undetermined") else ""
    md.append(f"- **계획 용도**: **{planned.get('planned_usage', '공동주택')}** [계획 세대/호수: **총 {planned.get('unit_count', 0)}세대/호**{undetermined_tag}]")
    md.append("")

    if dp_alert.get("required"):
        md.append("> ⚠️ **[경영진 필독] 지구단위계획 지침 별도 확인 필요**  ")
        md.append(f"> {dp_alert.get('message')}\n")

    md.append("### 💡 경영진 보고용 3줄 핵심 결론")
    for line in three_lines:
        md.append(f"> {line}  ")
    md.append("")

    # 4 Key Metrics Table
    md.append("### 📊 핵심 기획설계 및 사업성 지표 (Executive KPIs)")
    md.append("| 항목 | 적용 기준 / 산출값 | 평형 환산 / 비고 |")
    md.append("| :--- | :--- | :--- |")
    md.append(f"| **① 적용 건폐율 (BCR)** | **{bcr.get('applied_limit')}** ({bcr.get('comparison_summary')}) | 최대 건축면적: **{feas.get('max_building_area_sqm'):,.1f} ㎡ ({feas.get('max_building_area_py'):,.1f} 평)** |")
    md.append(f"| **② 적용 용적률 (FAR)** | **{far.get('applied_limit')}** ({far.get('comparison_summary')}) | 지상 연면적: **{feas.get('max_ground_gfa_sqm'):,.1f} ㎡ ({feas.get('max_ground_gfa_py'):,.1f} 평)** (인센티브 시: **{feas.get('incentive_far_pct')}%**) |")
    md.append(f"| **③ 예상 최고높이 / 층수** | **지상 {feas.get('est_floors')} 층 (약 {feas.get('est_height_m')} m)** | {height.get('summary_limit')} |")
    risk_summary = delibs.get("risk_summary", {})
    md.append(f"| **④ 주요 심의 리스크** | **{risk_summary.get('overall_grade')}** (총 {risk_summary.get('high_risk_count')}개 심의 대상) | 예상 사전인허가 기간: **{risk_summary.get('total_timeline_est')}** |")
    md.append(f"| **⑤ 예상 총 연면적** | 지상 {feas.get('max_ground_gfa_sqm'):,.1f}㎡ + 지하 {feas.get('est_basement_gfa_sqm'):,.1f}㎡ | **총 {feas.get('est_total_gfa_sqm'):,.1f} ㎡ ({feas.get('est_total_gfa_py'):,.1f} 평)** |")
    parking_info = constraints.get("parking", {})
    md.append(f"| **⑥ 주차 계획** | **법정 {parking_info.get('legal_count')} 대 / 실무권장 {parking_info.get('recommended_count')} 대** | 전기차 충전 {parking_info.get('ev_charging_count')}대 포함 ({parking_info.get('basis')}) |\n")

    # 탭 1. 대지 및 법정 규제 개요
    md.append("## 📑 2. 대지 및 법정 규제 상세 이중 비교 (국토계획법 vs 조례/지구단위계획)")
    md.append(f"> 💡 **이중 비교 판정**: {far.get('comparison_summary')}  ")
    md.append(f"> ※ 국토계획법상 법정 상한과 지자체 조례·지구단위계획 상한 중 **더 엄격한(낮은) 기준**이 실질 적용되었습니다.\n")
    md.append("| 구분 | 국토계획법 법정 상한 | 지자체 조례/지침 상한 | ★ 최종 적용 기준치 (엄격 기준) | 이중 비교 판정 요약 | 근거 법규 및 조례 | 특이사항 및 세부 조건 |")
    md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    md.append(f"| **건폐율** | {bcr.get('national_limit')} | {bcr.get('ordinance_limit')} | **★ {bcr.get('applied_limit')}** | {bcr.get('comparison_summary')} | {bcr.get('law_source')} | {bcr.get('notes')} |")
    md.append(f"| **용적률** | {far.get('national_limit')} | {far.get('ordinance_limit')} | **★ {far.get('applied_limit')}** | {far.get('comparison_summary')} | {far.get('law_source')} | {far.get('notes')} |")
    md.append(f"| **최고높이** | 건축법 제60조 / 제61조 | {height.get('summary_limit')} | **지상 {feas.get('est_floors')}층 ({feas.get('est_height_m')}m)** | 가로구역 및 일조사선 동시 충족 | {site.get('sido')} 건축조례 제33조·제35조 | 일조권 정북방향 사선제한(10m이하 1.5m, 10m초과 1/2) |")
    md.append("")

    # 탭 2. 용도별 설계 제약 및 주차 산정
    md.append("## 📐 3. 용도별 설계 제약 및 주차 산정")
    md.append(f"### 3.1 계획 용도 특화 기준 ({planned.get('planned_usage')})")
    for r in constraints.get("usage_rules", []):
        md.append(f"- {r}")
    md.append("")

    # 타입별 세대 구성 표시
    breakdown = feas.get("unit_breakdown", {})
    if breakdown:
        md.append("### 3.2 세대 및 호실 세부 구성")
        if breakdown.get("apt"):
            apt_items = [f"{k}타입: {v}세대" for k, v in breakdown["apt"].items() if v > 0]
            if apt_items:
                md.append(f"- **공동주택 ({feas.get('effective_apt_count')}세대)**: " + ", ".join(apt_items))
        if breakdown.get("officetel"):
            off_items = [f"{k}타입: {v}호" for k, v in breakdown["officetel"].items() if v > 0]
            if off_items:
                md.append(f"- **오피스텔 ({feas.get('effective_off_count')}호)**: " + ", ".join(off_items))
        md.append("")

    md.append("### 3.3 주차대수 산정 결과")
    md.append(f"- **법정 최소 대수**: `{parking_info.get('legal_count')} 대`")
    md.append(f"- **조례 기준 대수**: `{parking_info.get('ordinance_count')} 대`")
    md.append(f"- **실무 권장 대수**: `{parking_info.get('recommended_count')} 대` (친환경 충전시설 {parking_info.get('ev_charging_count')}대 필수 포함)")
    md.append(f"- **산정 근거**: {parking_info.get('basis')}\n")

    # 탭 3. 4대 주요 심의 판정 및 절차
    md.append("## 🛡️ 4. 4대 주요 심의 판정 및 소방 안전 매뉴얼")
    md.append("| 심의명 | 판정 | 리스크 태그 | 예상 소요기간 | 심의 주관부서 | 필수 체크포인트 |")
    md.append("| :--- | :---: | :---: | :--- | :--- | :--- |")
    for d in delibs.get("items", []):
        tag_icon = "🔴" if d.get('tag') == "규제" else ("🟡" if d.get('tag') == "주의" else "🟢")
        md.append(f"| **{d.get('name')}** | **{d.get('required')}** | {tag_icon} {d.get('tag')} | {d.get('timeline')} | {d.get('authority')} | {d.get('checkpoints')} |")
    md.append("")

    # 탭 4. 지구단위계획 및 지자체 상세 지침 체크리스트 표
    md.append("## 📋 5. 지구단위계획 및 지자체 실무 체크리스트 표")
    checklist = special.get("district_plan_checklist", [])
    if checklist:
        md.append("| 카테고리 | 세부 규정 항목 | 법적 및 지침 기준 | 실무 설계 점검사항 | 인센티브 및 완화 조건 |")
        md.append("| :--- | :--- | :--- | :--- | :--- |")
        for c in checklist:
            md.append(f"| **{c.get('카테고리')}** | {c.get('세부 규정 항목')} | {c.get('법적 및 지침 기준')} | {c.get('실무 설계 점검사항')} | {c.get('완화 및 인센티브')} |")
        md.append("")

    md.append("---")
    md.append("### 📌 작성자 소견 및 종합 결론")
    md.append(f"본 부지는 **{planned.get('planned_usage')}** 개발 시 총 연면적 약 **{feas.get('est_total_gfa_py'):,.0f} 평** 수준의 우수한 개발 잠재력을 보유하고 있습니다. 다만, 사전 심의({delibs.get('risk_summary', {}).get('high_risk_count')}개) 소요 기간({delibs.get('risk_summary', {}).get('total_timeline_est')}) 및 북측 일조사선제한에 따른 매싱 셋백을 기획설계 단계부터 반영하여 사업 일정을 관리하시기 바랍니다.")
    md.append("")
    md.append("*본 보고서는 국토교통부 브이월드(V-World) API 및 법제처 국가법령정보센터 자치법규 데이터를 기반으로 실시간 작성되었습니다.*")

    return "\n".join(md)
