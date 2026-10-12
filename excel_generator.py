"""
엑셀 보고서 생성 모듈 (Excel Report Generator)
- openpyxl을 활용한 경영진 보고용 고품질 서식 엑셀(.xlsx) 생성
- 4개 시트 구성:
  1. 종합요약_대지및법정규제
  2. 기획설계_세대구성_주차산정
  3. 4대심의_리스크매트릭스
  4. 지구단위계획_실무체크리스트
- 전문 스타일링: 네이비/슬레이트 헤더, 테두리, 숫자 포맷, 자동 열 너비 조정
"""

import io
from typing import Dict, Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# 스타일 상수 정의
FONT_TITLE = Font(name="맑은 고딕", size=15, bold=True, color="1E3A8A")
FONT_SECTION = Font(name="맑은 고딕", size=11, bold=True, color="0F172A")
FONT_HEADER = Font(name="맑은 고딕", size=9.5, bold=True, color="FFFFFF")
FONT_REGULAR = Font(name="맑은 고딕", size=9, color="1E293B")
FONT_BOLD = Font(name="맑은 고딕", size=9, bold=True, color="0F172A")
FONT_MUTED = Font(name="맑은 고딕", size=8.5, color="64748B")

FILL_NAVY_HEADER = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
FILL_BLUE_HEADER = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
FILL_SLATE_HEADER = PatternFill(start_color="475569", end_color="475569", fill_type="solid")
FILL_LIGHT_BLUE = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
FILL_LIGHT_GRAY = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
FILL_LIGHT_GREEN = PatternFill(start_color="DEF7EC", end_color="DEF7EC", fill_type="solid")
FILL_LIGHT_YELLOW = PatternFill(start_color="FEF08A", end_color="FEF08A", fill_type="solid")
FILL_LIGHT_RED = PatternFill(start_color="FDE8E8", end_color="FDE8E8", fill_type="solid")

BORDER_THIN = Border(
    left=Side(style="thin", color="CBD5E1"),
    right=Side(style="thin", color="CBD5E1"),
    top=Side(style="thin", color="CBD5E1"),
    bottom=Side(style="thin", color="CBD5E1")
)

ALIGN_CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
ALIGN_LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
ALIGN_RIGHT = Alignment(horizontal="right", vertical="center")

def _apply_box_title(ws, start_row: int, title_text: str, fill=FILL_NAVY_HEADER, font=FONT_HEADER, col_span=6):
    ws.merge_cells(start_row=start_row, start_column=1, end_row=start_row, end_column=col_span)
    cell = ws.cell(row=start_row, column=1, value=title_text)
    cell.font = font
    cell.fill = fill
    cell.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[start_row].height = 24

def _auto_fit_columns(ws, max_cols=8, min_width=12, max_width=45):
    for col_idx in range(1, max_cols + 1):
        col_letter = get_column_letter(col_idx)
        max_len = 0
        for cell in ws[col_letter]:
            val = str(cell.value or "")
            if "\n" in val:
                lines = val.split("\n")
                line_lens = [len(l.encode("cp949", errors="ignore")) for l in lines]
                max_len = max(max_len, max(line_lens) if line_lens else 0)
            else:
                max_len = max(max_len, len(val.encode("cp949", errors="ignore")))
        ws.column_dimensions[col_letter].width = max(min_width, min(max_width, max_len + 3))

def generate_excel_report(analysis: Dict[str, Any]) -> io.BytesIO:
    """분석 결과 딕셔너리를 입력받아 스타일링된 엑셀 바이트 스트림 반환"""
    wb = openpyxl.Workbook()
    # 기본 첫 시트 제거 또는 재사용
    ws1 = wb.active
    ws1.title = "대지및규제개요"

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
    parking_info = constraints.get("parking", {})

    # =========================================================================
    # 시트 1: 대지 및 규제 개요
    # =========================================================================
    ws1.views.sheetView[0].showGridLines = True
    
    # 상단 대제목
    ws1.merge_cells("A1:G1")
    title_cell = ws1["A1"]
    title_cell.value = "🏛️ [경영진 보고용] 건축 법규 및 사업성 통합 검토 리포트"
    title_cell.font = FONT_TITLE
    title_cell.alignment = Alignment(horizontal="left", vertical="center")
    ws1.row_dimensions[1].height = 32

    ws1["A2"].value = f"검토일자: 2026-10-12 | 대상 주소: {site.get('refined_address', site.get('raw_address'))} | 작성: AI 건축법규 분석에이전트"
    ws1["A2"].font = FONT_MUTED
    ws1.row_dimensions[2].height = 18

    # 1. 경영진 보고용 3줄 요약 결론
    row = 4
    _apply_box_title(ws1, row, "💡 1. 경영진 보고용 3줄 핵심 결론 (Executive Summary)", FILL_NAVY_HEADER, col_span=7)
    row += 1
    for idx, line in enumerate(three_lines, 1):
        ws1.merge_cells(start_row=row, start_column=1, end_row=row, end_column=7)
        c = ws1.cell(row=row, column=1, value=f"{idx}. {line}")
        c.font = FONT_BOLD
        c.fill = FILL_LIGHT_BLUE
        c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        for c_idx in range(1, 8):
            ws1.cell(row=row, column=c_idx).border = BORDER_THIN
        ws1.row_dimensions[row].height = 22
        row += 1

    # 2. 4대 핵심 지표 요약
    row += 1
    _apply_box_title(ws1, row, "📊 2. 핵심 기획설계 및 사업성 지표 (Executive KPIs)", FILL_BLUE_HEADER, col_span=7)
    row += 1
    headers_kpi = ["항목 구분", "적용 기준치", "산출 면적 / 규제 수치", "평형 환산 / 비고"]
    ws1.merge_cells(f"C{row}:D{row}")
    ws1.merge_cells(f"E{row}:G{row}")
    ws1.cell(row=row, column=1, value="항목 구분").font = FONT_HEADER
    ws1.cell(row=row, column=1).fill = FILL_SLATE_HEADER
    ws1.cell(row=row, column=2, value="적용 기준치").font = FONT_HEADER
    ws1.cell(row=row, column=2).fill = FILL_SLATE_HEADER
    ws1.cell(row=row, column=3, value="산출 면적 / 규제 수치").font = FONT_HEADER
    ws1.cell(row=row, column=3).fill = FILL_SLATE_HEADER
    ws1.cell(row=row, column=5, value="평형 환산 / 비고").font = FONT_HEADER
    ws1.cell(row=row, column=5).fill = FILL_SLATE_HEADER
    for c_idx in range(1, 8):
        ws1.cell(row=row, column=c_idx).border = BORDER_THIN
        ws1.cell(row=row, column=c_idx).alignment = ALIGN_CENTER
    ws1.row_dimensions[row].height = 20

    kpi_rows = [
        ("① 적용 건폐율 (BCR)", bcr.get("applied_limit"), f"{feas.get('max_building_area_sqm',0):,.1f} ㎡", f"{bcr.get('comparison_summary')} | 최대 건축면적 약 {feas.get('max_building_area_py',0):,.1f} 평"),
        ("② 적용 용적률 (FAR)", far.get("applied_limit"), f"{feas.get('max_ground_gfa_sqm',0):,.1f} ㎡", f"{far.get('comparison_summary')} | 지상 약 {feas.get('max_ground_gfa_py',0):,.1f} 평 (인센티브 시 {feas.get('incentive_far_pct')}%)"),
        ("③ 예상 최고높이 / 층수", height.get("summary_limit"), f"지상 {feas.get('est_floors')} 층", f"높이 약 {feas.get('est_height_m')} m (층당 {feas.get('floor_height_m')}m 기준)"),
        ("④ 주요 심의 리스크", delibs.get("risk_summary", {}).get("overall_grade"), f"총 {delibs.get('risk_summary', {}).get('high_risk_count')}개 대상", f"예상 사전인허가 기간: {delibs.get('risk_summary', {}).get('total_timeline_est')}"),
        ("⑤ 총 연면적 (지상+지하)", "지상 100% + 지하 45%", f"{feas.get('est_total_gfa_sqm',0):,.1f} ㎡", f"총 약 {feas.get('est_total_gfa_py',0):,.1f} 평 (지하 약 {feas.get('est_basement_gfa_sqm',0):,.1f}㎡)"),
        ("⑥ 계획 세대 / 주차", f"{planned.get('unit_count')} 세대/호", f"법정 {parking_info.get('legal_count')}대 / 권장 {parking_info.get('recommended_count')}대", f"친환경 충전 {parking_info.get('ev_charging_count')}대 포함 ({parking_info.get('basis')})")
    ]
    for kpi in kpi_rows:
        row += 1
        ws1.cell(row=row, column=1, value=kpi[0]).font = FONT_BOLD
        ws1.cell(row=row, column=1).alignment = ALIGN_LEFT
        ws1.cell(row=row, column=2, value=kpi[1]).font = FONT_BOLD
        ws1.cell(row=row, column=2).alignment = ALIGN_CENTER
        ws1.merge_cells(f"C{row}:D{row}")
        ws1.cell(row=row, column=3, value=kpi[2]).font = FONT_BOLD
        ws1.cell(row=row, column=3).alignment = ALIGN_CENTER
        ws1.merge_cells(f"E{row}:G{row}")
        ws1.cell(row=row, column=5, value=kpi[3]).font = FONT_REGULAR
        ws1.cell(row=row, column=5).alignment = ALIGN_LEFT
        for c_idx in range(1, 8):
            ws1.cell(row=row, column=c_idx).border = BORDER_THIN
        ws1.row_dimensions[row].height = 20

    # 3. 대지 지적 속성 및 토지대장 공부상 면적 검증
    row += 2
    _apply_box_title(ws1, row, "📍 3. 대지 지적 속성 및 토지대장 공부상 면적 검증 (V-World 연동)", FILL_NAVY_HEADER, col_span=7)
    row += 1

    match_str = "일치 (정상)" if area_val.get("is_match") else f"⚠️ 편차 {area_val.get('diff_sqm'):,.1f}㎡ ({area_val.get('diff_pct')}%)"
    prop_rows = [
        ("소재지 지번 주소", site.get("refined_address", ""), "필지고유번호 (PNU)", site.get("pnu", "")),
        ("법정 용도지역", land.get("primary_zoning", ""), "행정구역 체계", f"{site.get('sido')} {site.get('sigg')} {site.get('emd')}"),
        ("검토 대지면적", f"{planned.get('site_area_sqm',0):,.1f} ㎡ (약 {planned.get('site_area_py',0):,.1f}평)", "토지대장 공부상 면적", f"{area_val.get('official_area_sqm',0):,.1f} ㎡ (약 {area_val.get('official_area_py',0):,.1f}평)"),
        ("면적 정합성 검증", match_str, "공부상 지목 / 공시지가", f"{area_val.get('jimok')} / {area_val.get('official_price')}"),
        ("도로접면 / 지세", f"{area_val.get('road_side')} / {area_val.get('topography_height')}", "지구단위계획구역 여부", f"포함 ({', '.join(land.get('district_plan_names', []))})" if land.get("is_district_plan") else "해당없음 (일반조례 적용)"),
        ("기타 중첩 규제구역", ", ".join(land.get("overlay_zones", []) + land.get("restrictions", [])) or "특이 규제구역 없음", "경위도 WGS84 좌표", f"{site.get('x',0):.6f}, {site.get('y',0):.6f}")
    ]
    for pr in prop_rows:
        ws1.cell(row=row, column=1, value=pr[0]).font = FONT_BOLD
        ws1.cell(row=row, column=1).fill = FILL_LIGHT_GRAY
        ws1.cell(row=row, column=1).alignment = ALIGN_LEFT
        ws1.merge_cells(f"B{row}:C{row}")
        ws1.cell(row=row, column=2, value=pr[1]).font = FONT_REGULAR
        ws1.cell(row=row, column=2).alignment = ALIGN_LEFT

        ws1.cell(row=row, column=4, value=pr[2]).font = FONT_BOLD
        ws1.cell(row=row, column=4).fill = FILL_LIGHT_GRAY
        ws1.cell(row=row, column=4).alignment = ALIGN_LEFT
        ws1.merge_cells(f"E{row}:G{row}")
        ws1.cell(row=row, column=5, value=pr[3]).font = FONT_REGULAR
        ws1.cell(row=row, column=5).alignment = ALIGN_LEFT
        for c_idx in range(1, 8):
            ws1.cell(row=row, column=c_idx).border = BORDER_THIN
        ws1.row_dimensions[row].height = 20
        row += 1

    # 4. 법정 vs 지자체 조례 제한 비교표
    row += 1
    _apply_box_title(ws1, row, "⚖️ 4. 법정 vs 지자체 조례/지구단위계획 제한 이중 비교표", FILL_BLUE_HEADER, col_span=7)
    row += 1
    th = ["규제 항목", "최종 적용 (엄격)", "지자체 조례/지침 상한", "국토계획법 상한", "이중 비교 요약 및 근거 법규"]
    ws1.cell(row=row, column=1, value=th[0]).font = FONT_HEADER
    ws1.cell(row=row, column=1).fill = FILL_SLATE_HEADER
    ws1.cell(row=row, column=2, value=th[1]).font = FONT_HEADER
    ws1.cell(row=row, column=2).fill = FILL_SLATE_HEADER
    ws1.cell(row=row, column=3, value=th[2]).font = FONT_HEADER
    ws1.cell(row=row, column=3).fill = FILL_SLATE_HEADER
    ws1.cell(row=row, column=4, value=th[3]).font = FONT_HEADER
    ws1.cell(row=row, column=4).fill = FILL_SLATE_HEADER
    ws1.merge_cells(f"E{row}:G{row}")
    ws1.cell(row=row, column=5, value=th[4]).font = FONT_HEADER
    ws1.cell(row=row, column=5).fill = FILL_SLATE_HEADER
    for c_idx in range(1, 8):
        ws1.cell(row=row, column=c_idx).border = BORDER_THIN
        ws1.cell(row=row, column=c_idx).alignment = ALIGN_CENTER
    ws1.row_dimensions[row].height = 20

    comp_rows = [
        ("건폐율 (BCR)", f"★ {bcr.get('applied_limit')}", bcr.get("ordinance_limit"), bcr.get("national_limit"), f"{bcr.get('comparison_summary')} / {bcr.get('law_source')}"),
        ("용적률 (FAR)", f"★ {far.get('applied_limit')}", far.get("ordinance_limit"), far.get("national_limit"), f"{far.get('comparison_summary')} / {far.get('law_source')}"),
        ("최고높이 / 층수", f"지상 {feas.get('est_floors')}층", height.get("summary_limit"), "건축법 제60조 / 제61조", f"가로구역 및 일조사선 동시 충족 / {site.get('sido')} 건축조례")
    ]
    for cr in comp_rows:
        row += 1
        ws1.cell(row=row, column=1, value=cr[0]).font = FONT_BOLD
        ws1.cell(row=row, column=1).alignment = ALIGN_CENTER
        ws1.cell(row=row, column=2, value=cr[1]).font = FONT_BOLD
        ws1.cell(row=row, column=2).alignment = ALIGN_CENTER
        ws1.cell(row=row, column=3, value=cr[2]).font = FONT_REGULAR
        ws1.cell(row=row, column=3).alignment = ALIGN_CENTER
        ws1.cell(row=row, column=4, value=cr[3]).font = FONT_REGULAR
        ws1.cell(row=row, column=4).alignment = ALIGN_CENTER
        ws1.merge_cells(f"E{row}:G{row}")
        ws1.cell(row=row, column=5, value=cr[4]).font = FONT_REGULAR
        ws1.cell(row=row, column=5).alignment = ALIGN_LEFT
        for c_idx in range(1, 8):
            ws1.cell(row=row, column=c_idx).border = BORDER_THIN
        ws1.row_dimensions[row].height = 20
        for c_idx in range(1, 8):
            ws1.cell(row=row, column=c_idx).border = BORDER_THIN
        ws1.row_dimensions[row].height = 22

    # 5. 용적률 완화 및 인센티브 항목
    row += 2
    _apply_box_title(ws1, row, "🎁 5. 용적률 완화 및 인센티브 가능 항목 (기부채납·친환경)", FILL_NAVY_HEADER, col_span=7)
    row += 1
    ws1.cell(row=row, column=1, value="완화 구분").font = FONT_HEADER
    ws1.cell(row=row, column=1).fill = FILL_SLATE_HEADER
    ws1.cell(row=row, column=2, value="예상 완화율").font = FONT_HEADER
    ws1.cell(row=row, column=2).fill = FILL_SLATE_HEADER
    ws1.merge_cells(f"C{row}:D{row}")
    ws1.cell(row=row, column=3, value="필수 충족 조건").font = FONT_HEADER
    ws1.cell(row=row, column=3).fill = FILL_SLATE_HEADER
    ws1.merge_cells(f"E{row}:G{row}")
    ws1.cell(row=row, column=5, value="실무 적용 가이드").font = FONT_HEADER
    ws1.cell(row=row, column=5).fill = FILL_SLATE_HEADER
    for c_idx in range(1, 8):
        ws1.cell(row=row, column=c_idx).border = BORDER_THIN
        ws1.cell(row=row, column=c_idx).alignment = ALIGN_CENTER
    ws1.row_dimensions[row].height = 20

    for inc in analysis.get("incentives", []):
        row += 1
        ws1.cell(row=row, column=1, value=inc.get("항목", "")).font = FONT_BOLD
        ws1.cell(row=row, column=1).alignment = ALIGN_LEFT
        ws1.cell(row=row, column=2, value=inc.get("완화 범위", "")).font = FONT_BOLD
        ws1.cell(row=row, column=2).alignment = ALIGN_CENTER
        ws1.merge_cells(f"C{row}:D{row}")
        ws1.cell(row=row, column=3, value=inc.get("적용 조건", "")).font = FONT_REGULAR
        ws1.cell(row=row, column=3).alignment = ALIGN_LEFT
        ws1.merge_cells(f"E{row}:G{row}")
        ws1.cell(row=row, column=5, value=inc.get("비고", "")).font = FONT_REGULAR
        ws1.cell(row=row, column=5).alignment = ALIGN_LEFT
        for c_idx in range(1, 8):
            ws1.cell(row=row, column=c_idx).border = BORDER_THIN
        ws1.row_dimensions[row].height = 20

    _auto_fit_columns(ws1, max_cols=7)

    # =========================================================================
    # 시트 2: 기획설계_세대구성_주차산정
    # =========================================================================
    ws2 = wb.create_sheet(title="기획설계_세대구성_주차산정")
    ws2.views.sheetView[0].showGridLines = True

    ws2.merge_cells("A1:F1")
    title2 = ws2["A1"]
    title2.value = f"🏢 [{planned.get('planned_usage')}] 기획설계 세대 구성 및 주차대수 산정서"
    title2.font = FONT_TITLE
    title2.alignment = Alignment(horizontal="left", vertical="center")
    ws2.row_dimensions[1].height = 30

    row = 3
    _apply_box_title(ws2, row, "📐 1. 기획설계 개략 볼륨 및 건축 개요표", FILL_NAVY_HEADER, col_span=6)
    row += 1
    vol_h = ["사업성 지표 항목", "산출 면적 / 규모 (㎡)", "평형 환산 (평)", "적용 법규 및 산정 근거"]
    ws2.cell(row=row, column=1, value=vol_h[0]).font = FONT_HEADER
    ws2.cell(row=row, column=1).fill = FILL_SLATE_HEADER
    ws2.merge_cells(f"B{row}:C{row}")
    ws2.cell(row=row, column=2, value=vol_h[1]).font = FONT_HEADER
    ws2.cell(row=row, column=2).fill = FILL_SLATE_HEADER
    ws2.cell(row=row, column=4, value=vol_h[2]).font = FONT_HEADER
    ws2.cell(row=row, column=4).fill = FILL_SLATE_HEADER
    ws2.merge_cells(f"E{row}:F{row}")
    ws2.cell(row=row, column=5, value=vol_h[3]).font = FONT_HEADER
    ws2.cell(row=row, column=5).fill = FILL_SLATE_HEADER
    for c_idx in range(1, 7):
        ws2.cell(row=row, column=c_idx).border = BORDER_THIN
        ws2.cell(row=row, column=c_idx).alignment = ALIGN_CENTER
    ws2.row_dimensions[row].height = 20

    vol_items = [
        ("대지 면적", f"{planned.get('site_area_sqm',0):,.1f} ㎡", f"약 {planned.get('site_area_py',0):,.1f} 평", "토지대장 검증 기준"),
        ("최대 건축면적", f"{feas.get('max_building_area_sqm',0):,.1f} ㎡", f"약 {feas.get('max_building_area_py',0):,.1f} 평", f"건폐율 {bcr.get('ordinance_limit')} 적용"),
        ("지상 연면적 (기본)", f"{feas.get('max_ground_gfa_sqm',0):,.1f} ㎡", f"약 {feas.get('max_ground_gfa_py',0):,.1f} 평", f"조례 용적률 {far.get('ordinance_limit')} 적용"),
        ("지상 연면적 (인센티브)", f"{feas.get('incentive_ground_gfa_sqm',0):,.1f} ㎡", f"약 {feas.get('incentive_ground_gfa_py',0):,.1f} 평", f"완화 용적률 {feas.get('incentive_far_pct')}% 적용"),
        ("예상 지하층 연면적", f"{feas.get('est_basement_gfa_sqm',0):,.1f} ㎡", f"약 {round(feas.get('est_basement_gfa_sqm',0)/3.305785, 1):,.1f} 평", "주차장 및 기계전기실 (지상 대비 약 45%)"),
        ("예상 총 연면적", f"{feas.get('est_total_gfa_sqm',0):,.1f} ㎡", f"약 {feas.get('est_total_gfa_py',0):,.1f} 평", "지상 연면적 + 지하 연면적 합산"),
        ("예상 건물 규모", f"지상 {feas.get('est_floors')}층 / 지하 2~3층", f"최고높이 약 {feas.get('est_height_m')} m", "가로구역 및 정북사선 셋백 반영"),
        ("계획 총 세대/호수", f"{feas.get('effective_unit_count')} 세대/호", f"평균 전용 {feas.get('effective_unit_area')} ㎡", "규모 검토 및 세대구성 시뮬레이션 반영")
    ]
    for v in vol_items:
        row += 1
        ws2.cell(row=row, column=1, value=v[0]).font = FONT_BOLD
        ws2.cell(row=row, column=1).alignment = ALIGN_LEFT
        ws2.merge_cells(f"B{row}:C{row}")
        ws2.cell(row=row, column=2, value=v[1]).font = FONT_BOLD
        ws2.cell(row=row, column=2).alignment = ALIGN_CENTER
        ws2.cell(row=row, column=4, value=v[2]).font = FONT_REGULAR
        ws2.cell(row=row, column=4).alignment = ALIGN_CENTER
        ws2.merge_cells(f"E{row}:F{row}")
        ws2.cell(row=row, column=5, value=v[3]).font = FONT_REGULAR
        ws2.cell(row=row, column=5).alignment = ALIGN_LEFT
        for c_idx in range(1, 7):
            ws2.cell(row=row, column=c_idx).border = BORDER_THIN
        ws2.row_dimensions[row].height = 20

    # 2. 세대 및 호실 세부 구성표
    row += 2
    und_text = " (자동 추정 모드 적용)" if feas.get("is_undetermined") else " (사용자 상세 입력 적용)"
    _apply_box_title(ws2, row, f"🏘️ 2. 세대 및 호실 세부 구성 시뮬레이션{und_text}", FILL_BLUE_HEADER, col_span=6)
    row += 1
    ws2.cell(row=row, column=1, value="용도 구분").font = FONT_HEADER
    ws2.cell(row=row, column=1).fill = FILL_SLATE_HEADER
    ws2.cell(row=row, column=2, value="평형 타입").font = FONT_HEADER
    ws2.cell(row=row, column=2).fill = FILL_SLATE_HEADER
    ws2.cell(row=row, column=3, value="전용면적 (㎡)").font = FONT_HEADER
    ws2.cell(row=row, column=3).fill = FILL_SLATE_HEADER
    ws2.cell(row=row, column=4, value="평형 환산 (평)").font = FONT_HEADER
    ws2.cell(row=row, column=4).fill = FILL_SLATE_HEADER
    ws2.cell(row=row, column=5, value="계획 세대/호수").font = FONT_HEADER
    ws2.cell(row=row, column=5).fill = FILL_SLATE_HEADER
    ws2.cell(row=row, column=6, value="구성 비율 (%)").font = FONT_HEADER
    ws2.cell(row=row, column=6).fill = FILL_SLATE_HEADER
    for c_idx in range(1, 7):
        ws2.cell(row=row, column=c_idx).border = BORDER_THIN
        ws2.cell(row=row, column=c_idx).alignment = ALIGN_CENTER
    ws2.row_dimensions[row].height = 20

    breakdown = feas.get("unit_breakdown", {})
    tot_cnt = max(1, feas.get("effective_unit_count", 1))

    # 공동주택
    if breakdown.get("apt"):
        for k, v in breakdown["apt"].items():
            if v > 0:
                row += 1
                sqm = float(k)
                ws2.cell(row=row, column=1, value="공동주택 (아파트)").font = FONT_REGULAR
                ws2.cell(row=row, column=1).alignment = ALIGN_CENTER
                ws2.cell(row=row, column=2, value=f"{k} 타입").font = FONT_BOLD
                ws2.cell(row=row, column=2).alignment = ALIGN_CENTER
                ws2.cell(row=row, column=3, value=f"{sqm:,.1f} ㎡").font = FONT_REGULAR
                ws2.cell(row=row, column=3).alignment = ALIGN_CENTER
                ws2.cell(row=row, column=4, value=f"약 {round(sqm/3.305785, 1)} 평").font = FONT_REGULAR
                ws2.cell(row=row, column=4).alignment = ALIGN_CENTER
                ws2.cell(row=row, column=5, value=f"{v} 세대").font = FONT_BOLD
                ws2.cell(row=row, column=5).alignment = ALIGN_CENTER
                ws2.cell(row=row, column=6, value=f"{round(v/tot_cnt*100, 1)} %").font = FONT_REGULAR
                ws2.cell(row=row, column=6).alignment = ALIGN_CENTER
                for c_idx in range(1, 7):
                    ws2.cell(row=row, column=c_idx).border = BORDER_THIN
                ws2.row_dimensions[row].height = 20

    # 오피스텔
    if breakdown.get("officetel"):
        for k, v in breakdown["officetel"].items():
            if v > 0:
                row += 1
                sqm = float(k)
                ws2.cell(row=row, column=1, value="오피스텔 (업무시설)").font = FONT_REGULAR
                ws2.cell(row=row, column=1).alignment = ALIGN_CENTER
                ws2.cell(row=row, column=2, value=f"{k} 타입").font = FONT_BOLD
                ws2.cell(row=row, column=2).alignment = ALIGN_CENTER
                ws2.cell(row=row, column=3, value=f"{sqm:,.1f} ㎡").font = FONT_REGULAR
                ws2.cell(row=row, column=3).alignment = ALIGN_CENTER
                ws2.cell(row=row, column=4, value=f"약 {round(sqm/3.305785, 1)} 평").font = FONT_REGULAR
                ws2.cell(row=row, column=4).alignment = ALIGN_CENTER
                ws2.cell(row=row, column=5, value=f"{v} 호").font = FONT_BOLD
                ws2.cell(row=row, column=5).alignment = ALIGN_CENTER
                ws2.cell(row=row, column=6, value=f"{round(v/tot_cnt*100, 1)} %").font = FONT_REGULAR
                ws2.cell(row=row, column=6).alignment = ALIGN_CENTER
                for c_idx in range(1, 7):
                    ws2.cell(row=row, column=c_idx).border = BORDER_THIN
                ws2.row_dimensions[row].height = 20

    # 합계 행
    row += 1
    ws2.merge_cells(f"A{row}:D{row}")
    ws2.cell(row=row, column=1, value="총 계획 세대/호수 합계").font = FONT_BOLD
    ws2.cell(row=row, column=1).fill = FILL_LIGHT_BLUE
    ws2.cell(row=row, column=1).alignment = ALIGN_CENTER
    ws2.cell(row=row, column=5, value=f"{feas.get('effective_unit_count')} 세대/호").font = FONT_BOLD
    ws2.cell(row=row, column=5).fill = FILL_LIGHT_BLUE
    ws2.cell(row=row, column=5).alignment = ALIGN_CENTER
    ws2.cell(row=row, column=6, value="100.0 %").font = FONT_BOLD
    ws2.cell(row=row, column=6).fill = FILL_LIGHT_BLUE
    ws2.cell(row=row, column=6).alignment = ALIGN_CENTER
    for c_idx in range(1, 7):
        ws2.cell(row=row, column=c_idx).border = BORDER_THIN
    ws2.row_dimensions[row].height = 22

    # 3. 주차대수 자동 산정 결과
    row += 2
    _apply_box_title(ws2, row, "🅿️ 3. 법정 및 지자체 조례 기준 주차대수 자동 산정 매트릭스", FILL_NAVY_HEADER, col_span=6)
    row += 1
    p_h = ["구분 항목", "산정 주차대수", "적용 근거 법령 및 조례", "특이사항 및 충족 요건"]
    ws2.cell(row=row, column=1, value=p_h[0]).font = FONT_HEADER
    ws2.cell(row=row, column=1).fill = FILL_SLATE_HEADER
    ws2.cell(row=row, column=2, value=p_h[1]).font = FONT_HEADER
    ws2.cell(row=row, column=2).fill = FILL_SLATE_HEADER
    ws2.merge_cells(f"C{row}:D{row}")
    ws2.cell(row=row, column=3, value=p_h[2]).font = FONT_HEADER
    ws2.cell(row=row, column=3).fill = FILL_SLATE_HEADER
    ws2.merge_cells(f"E{row}:F{row}")
    ws2.cell(row=row, column=5, value=p_h[3]).font = FONT_HEADER
    ws2.cell(row=row, column=5).fill = FILL_SLATE_HEADER
    for c_idx in range(1, 7):
        ws2.cell(row=row, column=c_idx).border = BORDER_THIN
        ws2.cell(row=row, column=c_idx).alignment = ALIGN_CENTER
    ws2.row_dimensions[row].height = 20

    park_items = [
        ("법정 최소 주차대수", f"{parking_info.get('legal_count')} 대", "주차장법 시행령 별표1", "시설면적 및 전용면적 기준 법적 최소 대수"),
        ("지자체 조례 기준 대수", f"{parking_info.get('ordinance_count')} 대", f"{site.get('sido')} 주차장 설치 및 관리 조례", "지자체 강화 조례 기준 반영"),
        ("★ 실무 권장 주차대수", f"{parking_info.get('recommended_count')} 대", "분양성 및 건축심의 권고 반영 (세대당 1.1~1.3대)", "심의 원안 통과 및 입주자 만족도 확보 권장치"),
        ("친환경차 충전시설", f"{parking_info.get('ev_charging_count')} 대", "친환경자동차법 제11조의2", "총 주차대수의 5% 이상 의무 설치 (급속/완속)"),
        ("장애인 전용 주차구획", f"{parking_info.get('accessibility_count')} 대", "장애인등편의법", "전체 주차구획의 2~4% 범위 법정 의무 구획")
    ]
    for pi in park_items:
        row += 1
        ws2.cell(row=row, column=1, value=pi[0]).font = FONT_BOLD
        ws2.cell(row=row, column=1).alignment = ALIGN_LEFT
        ws2.cell(row=row, column=2, value=pi[1]).font = FONT_BOLD
        ws2.cell(row=row, column=2).alignment = ALIGN_CENTER
        ws2.merge_cells(f"C{row}:D{row}")
        ws2.cell(row=row, column=3, value=pi[2]).font = FONT_REGULAR
        ws2.cell(row=row, column=3).alignment = ALIGN_LEFT
        ws2.merge_cells(f"E{row}:F{row}")
        ws2.cell(row=row, column=5, value=pi[3]).font = FONT_REGULAR
        ws2.cell(row=row, column=5).alignment = ALIGN_LEFT
        for c_idx in range(1, 7):
            ws2.cell(row=row, column=c_idx).border = BORDER_THIN
        ws2.row_dimensions[row].height = 20

    _auto_fit_columns(ws2, max_cols=6)

    # =========================================================================
    # 시트 3: 4대심의_리스크매트릭스
    # =========================================================================
    ws3 = wb.create_sheet(title="4대심의_리스크매트릭스")
    ws3.views.sheetView[0].showGridLines = True

    ws3.merge_cells("A1:G1")
    title3 = ws3["A1"]
    title3.value = "🛡️ 4대 주요 심의 자동 판정 (O/X) 및 소방 안전 매뉴얼"
    title3.font = FONT_TITLE
    title3.alignment = Alignment(horizontal="left", vertical="center")
    ws3.row_dimensions[1].height = 30

    row = 3
    _apply_box_title(ws3, row, "🛡️ 1. 4대 주요 심의 자동 판정 매트릭스", FILL_NAVY_HEADER, col_span=7)
    row += 1
    d_h = ["심의 명칭", "대상 여부", "리스크 등급", "예상 소요기간", "심의 주관기관", "핵심 체크포인트 및 판정 기준", "필수 제출 도서"]
    for i, h in enumerate(d_h, 1):
        ws3.cell(row=row, column=i, value=h).font = FONT_HEADER
        ws3.cell(row=row, column=i).fill = FILL_SLATE_HEADER
        ws3.cell(row=row, column=i).border = BORDER_THIN
        ws3.cell(row=row, column=i).alignment = ALIGN_CENTER
    ws3.row_dimensions[row].height = 20

    for d in delibs.get("items", []):
        row += 1
        ws3.cell(row=row, column=1, value=d.get("name")).font = FONT_BOLD
        ws3.cell(row=row, column=1).alignment = ALIGN_CENTER

        req_cell = ws3.cell(row=row, column=2, value=d.get("required"))
        req_cell.font = FONT_BOLD
        req_cell.alignment = ALIGN_CENTER
        if "대상" in str(d.get("required")):
            req_cell.fill = FILL_LIGHT_RED if d.get("tag") == "규제" else FILL_LIGHT_YELLOW

        tag_cell = ws3.cell(row=row, column=3, value=d.get("tag"))
        tag_cell.font = FONT_BOLD
        tag_cell.alignment = ALIGN_CENTER
        if d.get("tag") == "규제":
            tag_cell.fill = FILL_LIGHT_RED
        elif d.get("tag") == "주의":
            tag_cell.fill = FILL_LIGHT_YELLOW
        else:
            tag_cell.fill = FILL_LIGHT_GREEN

        ws3.cell(row=row, column=4, value=d.get("timeline")).font = FONT_REGULAR
        ws3.cell(row=row, column=4).alignment = ALIGN_CENTER
        ws3.cell(row=row, column=5, value=d.get("authority")).font = FONT_REGULAR
        ws3.cell(row=row, column=5).alignment = ALIGN_CENTER
        ws3.cell(row=row, column=6, value=d.get("checkpoints")).font = FONT_REGULAR
        ws3.cell(row=row, column=6).alignment = ALIGN_LEFT
        ws3.cell(row=row, column=7, value=d.get("docs")).font = FONT_MUTED
        ws3.cell(row=row, column=7).alignment = ALIGN_LEFT

        for c_idx in range(1, 8):
            ws3.cell(row=row, column=c_idx).border = BORDER_THIN
        ws3.row_dimensions[row].height = 24

    row += 2
    _apply_box_title(ws3, row, "🚒 2. 피난 / 방화 / 소방 안전 필수 특이사항 매뉴얼", FILL_BLUE_HEADER, col_span=7)
    row += 1
    for note in delibs.get("fire_safety_notes", []):
        ws3.merge_cells(start_row=row, start_column=1, end_row=row, end_column=7)
        c = ws3.cell(row=row, column=1, value=f"- {note}")
        c.font = FONT_REGULAR
        c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        for c_idx in range(1, 8):
            ws3.cell(row=row, column=c_idx).border = BORDER_THIN
        ws3.row_dimensions[row].height = 20
        row += 1

    _auto_fit_columns(ws3, max_cols=7)

    # =========================================================================
    # 시트 4: 지구단위계획_실무체크리스트
    # =========================================================================
    ws4 = wb.create_sheet(title="지구단위계획_실무체크리스트")
    ws4.views.sheetView[0].showGridLines = True

    ws4.merge_cells("A1:E1")
    title4 = ws4["A1"]
    title4.value = "📋 지구단위계획 6대 핵심 지침 실무 점검 체크리스트 표"
    title4.font = FONT_TITLE
    title4.alignment = Alignment(horizontal="left", vertical="center")
    ws4.row_dimensions[1].height = 30

    row = 3
    _apply_box_title(ws4, row, f"🏛️ 1. {site.get('sido')} 건축조례 및 지자체 특별 규정 하이라이트", FILL_NAVY_HEADER, col_span=5)
    row += 1
    for sh in special.get("special_highlights", []):
        ws4.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
        c = ws4.cell(row=row, column=1, value=f"- {sh}")
        c.font = FONT_REGULAR
        c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        for c_idx in range(1, 6):
            ws4.cell(row=row, column=c_idx).border = BORDER_THIN
        ws4.row_dimensions[row].height = 20
        row += 1

    row += 1
    _apply_box_title(ws4, row, "📋 2. 지구단위계획 6대 핵심 지침 실무 체크리스트 (설계 반영 의무)", FILL_BLUE_HEADER, col_span=5)
    row += 1
    dp_h = ["구분 카테고리", "세부 규정 항목", "법적 및 지침 기준", "실무 설계 점검사항", "인센티브 및 완화 조건"]
    for i, h in enumerate(dp_h, 1):
        ws4.cell(row=row, column=i, value=h).font = FONT_HEADER
        ws4.cell(row=row, column=i).fill = FILL_SLATE_HEADER
        ws4.cell(row=row, column=i).border = BORDER_THIN
        ws4.cell(row=row, column=i).alignment = ALIGN_CENTER
    ws4.row_dimensions[row].height = 20

    for chk in special.get("district_plan_checklist", []):
        row += 1
        ws4.cell(row=row, column=1, value=chk.get("카테고리")).font = FONT_BOLD
        ws4.cell(row=row, column=1).alignment = ALIGN_CENTER
        ws4.cell(row=row, column=2, value=chk.get("세부 규정 항목")).font = FONT_BOLD
        ws4.cell(row=row, column=2).alignment = ALIGN_CENTER
        ws4.cell(row=row, column=3, value=chk.get("법적 및 지침 기준")).font = FONT_REGULAR
        ws4.cell(row=row, column=3).alignment = ALIGN_LEFT
        ws4.cell(row=row, column=4, value=chk.get("실무 설계 점검사항")).font = FONT_REGULAR
        ws4.cell(row=row, column=4).alignment = ALIGN_LEFT
        ws4.cell(row=row, column=5, value=chk.get("완화 및 인센티브")).font = FONT_REGULAR
        ws4.cell(row=row, column=5).alignment = ALIGN_LEFT

        for c_idx in range(1, 6):
            ws4.cell(row=row, column=c_idx).border = BORDER_THIN
        ws4.row_dimensions[row].height = 26

    _auto_fit_columns(ws4, max_cols=5, max_width=50)

    # 바이트 스트림 변환
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer
