"""
🏛️ AI 건축 법규 및 기획설계 사업성 통합 검토 웹 앱 (Streamlit)
- 보고용 대시보드 UI
- 대지 주소 + 계획 용도 + 대지면적 입력 기반
- 브이월드 API (PNU, 좌표, 용도지역, 토지대장 공부상 면적) + 법제처 Open API 연동
- 상단 Executive Summary & 4대 핵심 지표 카드
- 5대 전문 탭 (대지규제 / 설계제약 및 주차 / 4대 심의 판정 / 지구단위계획 / 보고서용 결론)
- [업그레이드 1] 대지면적 검증 및 토지대장 공부상 면적 1-클릭 적용
- [업그레이드 2] 복합 용도 세대/타입별 상세 입력 (공동주택 59/74/84/104 + 오피스텔 29/39/59/84) 및 세대 구성 미정 자동 추정
- [업그레이드 3] 지구단위계획 6대 핵심 지침 실무 체크리스트 표 (건축선, 용도, 공공보행통로, 인센티브, 높이, 가로활성화)
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional

from vworld_api import VWorldClient
from moleg_api import MolegClient
from regulation_engine import RegulationEngine
from report_generator import generate_markdown_report
from excel_generator import generate_excel_report
from document_generator import generate_docx_report

# -------------------------------------------------------------
# 페이지 설정
# -------------------------------------------------------------
st.set_page_config(
    page_title="건축 법규 및 사업성 통합 검토 리포트",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------
# 보고용 커스텀 CSS 스타일링
# -------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
    }
    
    .report-badge {
        display: inline-block;
        background: #1E293B;
        color: #F8FAFC;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 4px;
        margin-right: 6px;
        letter-spacing: 0.5px;
    }
    .exec-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #0F172A;
        margin-top: 0.2rem;
        margin-bottom: 0.3rem;
        letter-spacing: -0.5px;
    }
    .exec-sub {
        font-size: 1.0rem;
        color: #475569;
        margin-bottom: 1.2rem;
    }
    
    /* Executive Metric Cards */
    .metric-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-top: 4px solid #2563EB;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .metric-box.orange { border-top-color: #F59E0B; }
    .metric-box.green { border-top-color: #10B981; }
    .metric-box.purple { border-top-color: #8B5CF6; }
    .metric-box.red { border-top-color: #EF4444; }

    .metric-header {
        font-size: 0.85rem;
        color: #64748B;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .metric-value-lg {
        font-size: 1.6rem;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.2;
    }
    .metric-footnote {
        font-size: 0.8rem;
        color: #64748B;
        margin-top: 6px;
        padding-top: 6px;
        border-top: 1px dashed #E2E8F0;
    }

    /* Executive 3-line Conclusion Card */
    .conclusion-box {
        background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%);
        border: 1px solid #BFDBFE;
        border-left: 6px solid #2563EB;
        border-radius: 8px;
        padding: 18px 20px;
        margin: 1.2rem 0;
    }
    .conclusion-box h4 {
        margin: 0 0 10px 0;
        color: #1E3A8A;
        font-size: 1.15rem;
        font-weight: 800;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .conclusion-item {
        font-size: 0.95rem;
        line-height: 1.65;
        color: #1E293B;
        margin-bottom: 6px;
    }

    /* Alert Box */
    .warning-alert {
        background-color: #FFFBEB;
        border: 1px solid #FCD34D;
        border-left: 5px solid #F59E0B;
        padding: 14px 18px;
        border-radius: 6px;
        margin-bottom: 1.2rem;
        color: #92400E;
    }

    /* Status Tags */
    .tag-green {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 0.8rem;
    }
    .tag-yellow {
        background-color: #FEF08A;
        color: #713F12;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 0.8rem;
    }
    .tag-red {
        background-color: #FDE8E8;
        color: #9B1C1C;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 0.8rem;
    }
    
    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1E293B;
        margin-top: 1.0rem;
        margin-bottom: 0.8rem;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 6px;
    }

    .checklist-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 클라이언트 초기화
# -------------------------------------------------------------
@st.cache_resource
def get_api_clients():
    vworld = VWorldClient()
    moleg = MolegClient()
    return vworld, moleg

vworld, moleg = get_api_clients()
engine = RegulationEngine()

# -------------------------------------------------------------
# 세션 상태 초기값 설정
# -------------------------------------------------------------
if "target_addr" not in st.session_state:
    st.session_state["target_addr"] = "서울시 성북구 길음동 1284"

if "site_area_sqm_val" not in st.session_state:
    st.session_state["site_area_sqm_val"] = 46111.5

if "cadastral_info" not in st.session_state:
    # 최초 진입 시 기본 주소 토지대장 데이터 미리 로드
    pnu_init = "1129013400112840000"
    st.session_state["cadastral_info"] = vworld.get_official_cadastral_info(pnu_init)

if "apt_types" not in st.session_state:
    st.session_state["apt_types"] = [
        {"area": 59.0, "count": 80},
        {"area": 84.0, "count": 120}
    ]

if "off_types" not in st.session_state:
    st.session_state["off_types"] = [
        {"area": 29.0, "count": 30},
        {"area": 59.0, "count": 40}
    ]

# -------------------------------------------------------------
# 사이드바: 기획설계 조건 및 검토 조건 입력
# -------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/building.png", width=65)
    st.markdown("### 📋 기획설계 조건 설정")
    st.caption("실무 설계 및 보고용 계획 조건을 설정하세요.")

    # 1. 계획 용도
    planned_usage = st.selectbox(
        "1️⃣ 계획 용도 선택",
        options=[
            "주상복합 (주거복합건축물)",
            "공동주택 (아파트)",
            "오피스텔 (업무시설)",
            "근린생활시설 / 판매시설",
            "일반 업무시설 (오피스)"
        ],
        index=0
    )

    # 2. 대지 면적 및 토지대장 검증
    st.markdown("---")
    st.markdown("#### 📐 2️⃣ 대지 면적 설정 및 공부 검증")
    
    site_area_sqm = st.number_input(
        "검토 대지 면적 (㎡)",
        min_value=0.0,
        max_value=500000.0,
        value=float(st.session_state["site_area_sqm_val"]),
        step=50.0,
        help="검토할 필지의 대지면적을 입력하세요."
    )
    # 세션 상태 동기화
    st.session_state["site_area_sqm_val"] = site_area_sqm
    site_area_py = round(site_area_sqm / 3.305785, 1)
    st.caption(f"📐 평형 환산: **약 {site_area_py:,.1f} 평**")

    # 🌟 토지대장 공부상 면적 비교 및 1-클릭 적용 기능
    cad_info = st.session_state.get("cadastral_info", {})
    if cad_info and cad_info.get("has_cadastral"):
        official_sqm = cad_info.get("official_area_sqm", 0.0)
        official_py = cad_info.get("official_area_py", 0.0)
        diff_sqm = abs(site_area_sqm - official_sqm)
        diff_pct = (diff_sqm / official_sqm * 100.0) if official_sqm > 0 else 0.0

        if diff_sqm > 1.0:
            st.warning(
                f"⚠️ **토지대장 면적과 편차 발생**\n"
                f"- 공부상 면적: **{official_sqm:,.1f}㎡** ({official_py:,.1f}평)\n"
                f"- 편차: **{diff_sqm:,.1f}㎡** ({diff_pct:.1f}%)\n"
                f"- 지목: `{cad_info.get('jimok')}` | 공시지가: `{cad_info.get('official_price')}`"
            )
            if st.button(f"📋 공부상 면적 적용 ({official_sqm:,.1f}㎡)", use_container_width=True, type="secondary"):
                st.session_state["site_area_sqm_val"] = float(official_sqm)
                st.rerun()
        else:
            st.success(
                f"✅ **토지대장 면적 일치**\n"
                f"- 공부상: **{official_sqm:,.1f}㎡** ({official_py:,.1f}평)\n"
                f"- 지목: `{cad_info.get('jimok')}` | 도로: `{cad_info.get('road_side')}`"
            )

    # 3. 세대 및 호실 구성 상세 입력 (미정 체크박스 및 복합용도 분리)
    st.markdown("---")
    st.markdown("#### 🏢 3️⃣ 세대 구성 및 규모 설정")

    is_units_undetermined = st.checkbox(
        "📐 세대 구성 미정 (규모 검토 중)",
        value=False,
        help="체크 시 법정 최대 용적률 및 시장 표준 비율(공동주택 75% 전용률, 오피스텔 50% 전용률)로 세대 구성을 자동 추정합니다."
    )

    unit_breakdown: Optional[Dict[str, Any]] = None
    unit_count = 100
    unit_area = 84.0

    if is_units_undetermined:
        st.info("💡 **[규모 검토 모드]** 용적률 상한 및 시장 표준 비율(국민평형 84/59 등)에 맞춰 최적 세대수가 자동 산출됩니다.")
        unit_breakdown = None
    else:
        # 용도별 세대 구성 동적 자유 입력 (타입 추가/삭제 및 실시간 연동)
        if "주상복합" in planned_usage:
            # 1. 공동주택 세대 구성
            st.markdown("**🏢 [공동주택 세대 구성]**")
            st.caption("전용면적(㎡)과 계획 세대수를 자유롭게 입력하세요.")

            apt_dict = {}
            apt_total = 0
            if not st.session_state["apt_types"]:
                st.info("💡 등록된 타입이 없습니다. 아래 버튼으로 추가하세요.")

            for i, it in enumerate(st.session_state["apt_types"]):
                c_area, c_cnt, c_del = st.columns([1.6, 1.4, 0.6])
                with c_area:
                    a_val = st.number_input(
                        f"전용(㎡) #{i+1}",
                        min_value=10.0,
                        max_value=500.0,
                        value=float(it["area"]),
                        step=0.5,
                        format="%.1f",
                        key=f"sb_apt_area_{i}",
                        help="전용면적 직접 입력 (예: 59.0, 72.5, 84.0)"
                    )
                with c_cnt:
                    c_val = st.number_input(
                        f"세대수 #{i+1}",
                        min_value=0,
                        max_value=5000,
                        value=int(it["count"]),
                        step=5,
                        key=f"sb_apt_cnt_{i}",
                        help="해당 타입의 계획 세대수"
                    )
                with c_del:
                    st.write("<div style='height:28px;'></div>", unsafe_allow_html=True)
                    if st.button("✕", key=f"sb_apt_del_{i}", help=f"#{i+1} 타입 삭제"):
                        st.session_state["apt_types"].pop(i)
                        st.rerun()

                it["area"] = a_val
                it["count"] = c_val
                k = f"{a_val:.1f}".rstrip('0').rstrip('.')
                apt_dict[k] = apt_dict.get(k, 0) + c_val
                apt_total += c_val
                st.caption(f"↳ #{i+1}: 전용 {a_val:.1f}㎡ (약 {round(a_val/3.305785, 1)}평) × **{c_val}세대**")

            if st.button("➕ 공동주택 타입 추가", use_container_width=True, key="btn_add_apt_type"):
                next_area = 74.0 if len(st.session_state["apt_types"]) >= 2 else 84.0
                st.session_state["apt_types"].append({"area": next_area, "count": 20})
                st.rerun()

            st.caption(f"↳ 공동주택 소계: **{apt_total} 세대**")
            st.markdown("---")

            # 2. 오피스텔 호실 구성
            st.markdown("**🏬 [오피스텔 호실 구성]**")
            st.caption("전용면적(㎡)과 계획 호실수를 자유롭게 입력하세요.")

            off_dict = {}
            off_total = 0
            if not st.session_state["off_types"]:
                st.info("💡 등록된 타입이 없습니다. 아래 버튼으로 추가하세요.")

            for i, it in enumerate(st.session_state["off_types"]):
                c_area, c_cnt, c_del = st.columns([1.6, 1.4, 0.6])
                with c_area:
                    a_val = st.number_input(
                        f"전용(㎡) #{i+1}",
                        min_value=10.0,
                        max_value=500.0,
                        value=float(it["area"]),
                        step=0.5,
                        format="%.1f",
                        key=f"sb_off_area_{i}",
                        help="전용면적 직접 입력 (예: 29.0, 39.5, 59.0)"
                    )
                with c_cnt:
                    c_val = st.number_input(
                        f"호실수 #{i+1}",
                        min_value=0,
                        max_value=5000,
                        value=int(it["count"]),
                        step=5,
                        key=f"sb_off_cnt_{i}",
                        help="해당 타입의 계획 호실수"
                    )
                with c_del:
                    st.write("<div style='height:28px;'></div>", unsafe_allow_html=True)
                    if st.button("✕", key=f"sb_off_del_{i}", help=f"#{i+1} 타입 삭제"):
                        st.session_state["off_types"].pop(i)
                        st.rerun()

                it["area"] = a_val
                it["count"] = c_val
                k = f"{a_val:.1f}".rstrip('0').rstrip('.')
                off_dict[k] = off_dict.get(k, 0) + c_val
                off_total += c_val
                st.caption(f"↳ #{i+1}: 전용 {a_val:.1f}㎡ (약 {round(a_val/3.305785, 1)}평) × **{c_val}호**")

            if st.button("➕ 오피스텔 타입 추가", use_container_width=True, key="btn_add_off_type"):
                next_area = 39.0 if len(st.session_state["off_types"]) >= 2 else 59.0
                st.session_state["off_types"].append({"area": next_area, "count": 20})
                st.rerun()

            st.caption(f"↳ 오피스텔 소계: **{off_total} 호실**")

            unit_count = apt_total + off_total
            unit_breakdown = {
                "apt": apt_dict,
                "officetel": off_dict
            }
            st.success(f"📊 **총 계획 규모: {unit_count} 세대/호** (아파트 {apt_total} + 오피스텔 {off_total})")

        elif "공동주택" in planned_usage:
            st.markdown("**🏢 [공동주택 세대 구성]**")
            st.caption("전용면적(㎡)과 계획 세대수를 자유롭게 입력하세요.")

            apt_dict = {}
            apt_total = 0
            if not st.session_state["apt_types"]:
                st.info("💡 등록된 타입이 없습니다. 아래 버튼으로 추가하세요.")

            for i, it in enumerate(st.session_state["apt_types"]):
                c_area, c_cnt, c_del = st.columns([1.6, 1.4, 0.6])
                with c_area:
                    a_val = st.number_input(
                        f"전용(㎡) #{i+1}",
                        min_value=10.0,
                        max_value=500.0,
                        value=float(it["area"]),
                        step=0.5,
                        format="%.1f",
                        key=f"sb_apt_only_area_{i}",
                        help="전용면적 직접 입력 (예: 59.0, 72.5, 84.0)"
                    )
                with c_cnt:
                    c_val = st.number_input(
                        f"세대수 #{i+1}",
                        min_value=0,
                        max_value=5000,
                        value=int(it["count"]),
                        step=5,
                        key=f"sb_apt_only_cnt_{i}",
                        help="해당 타입의 계획 세대수"
                    )
                with c_del:
                    st.write("<div style='height:28px;'></div>", unsafe_allow_html=True)
                    if st.button("✕", key=f"sb_apt_only_del_{i}", help=f"#{i+1} 타입 삭제"):
                        st.session_state["apt_types"].pop(i)
                        st.rerun()

                it["area"] = a_val
                it["count"] = c_val
                k = f"{a_val:.1f}".rstrip('0').rstrip('.')
                apt_dict[k] = apt_dict.get(k, 0) + c_val
                apt_total += c_val
                st.caption(f"↳ #{i+1}: 전용 {a_val:.1f}㎡ (약 {round(a_val/3.305785, 1)}평) × **{c_val}세대**")

            if st.button("➕ 공동주택 타입 추가", use_container_width=True, key="btn_add_apt_only_type"):
                next_area = 74.0 if len(st.session_state["apt_types"]) >= 2 else 84.0
                st.session_state["apt_types"].append({"area": next_area, "count": 20})
                st.rerun()

            unit_count = apt_total
            unit_breakdown = {
                "apt": apt_dict,
                "officetel": {}
            }
            st.success(f"📊 **공동주택 총 세대수: {unit_count} 세대**")

        elif "오피스텔" in planned_usage:
            st.markdown("**🏬 [오피스텔 호실 구성]**")
            st.caption("전용면적(㎡)과 계획 호실수를 자유롭게 입력하세요.")

            off_dict = {}
            off_total = 0
            if not st.session_state["off_types"]:
                st.info("💡 등록된 타입이 없습니다. 아래 버튼으로 추가하세요.")

            for i, it in enumerate(st.session_state["off_types"]):
                c_area, c_cnt, c_del = st.columns([1.6, 1.4, 0.6])
                with c_area:
                    a_val = st.number_input(
                        f"전용(㎡) #{i+1}",
                        min_value=10.0,
                        max_value=500.0,
                        value=float(it["area"]),
                        step=0.5,
                        format="%.1f",
                        key=f"sb_off_only_area_{i}",
                        help="전용면적 직접 입력 (예: 29.0, 39.5, 59.0)"
                    )
                with c_cnt:
                    c_val = st.number_input(
                        f"호실수 #{i+1}",
                        min_value=0,
                        max_value=5000,
                        value=int(it["count"]),
                        step=5,
                        key=f"sb_off_only_cnt_{i}",
                        help="해당 타입의 계획 호실수"
                    )
                with c_del:
                    st.write("<div style='height:28px;'></div>", unsafe_allow_html=True)
                    if st.button("✕", key=f"sb_off_only_del_{i}", help=f"#{i+1} 타입 삭제"):
                        st.session_state["off_types"].pop(i)
                        st.rerun()

                it["area"] = a_val
                it["count"] = c_val
                k = f"{a_val:.1f}".rstrip('0').rstrip('.')
                off_dict[k] = off_dict.get(k, 0) + c_val
                off_total += c_val
                st.caption(f"↳ #{i+1}: 전용 {a_val:.1f}㎡ (약 {round(a_val/3.305785, 1)}평) × **{c_val}호**")

            if st.button("➕ 오피스텔 타입 추가", use_container_width=True, key="btn_add_off_only_type"):
                next_area = 39.0 if len(st.session_state["off_types"]) >= 2 else 59.0
                st.session_state["off_types"].append({"area": next_area, "count": 20})
                st.rerun()

            unit_count = off_total
            unit_breakdown = {
                "apt": {},
                "officetel": off_dict
            }
            st.success(f"📊 **오피스텔 총 호실수: {unit_count} 호실**")

        else:
            unit_count = st.number_input("예상 실/호수 (규모)", min_value=1, max_value=2000, value=60, step=10)
            unit_area = st.number_input("호실당 전용면적 (㎡)", min_value=10.0, max_value=1000.0, value=85.0, step=10.0)
            unit_breakdown = None

    # 4. 지자체 조례 및 지구단위계획 상한 보정 (사용자 수동 오버라이드)
    st.markdown("---")
    st.markdown("#### ⚖️ 4️⃣ 지자체 조례 및 지구단위계획 상한 보정")
    st.caption("특정 조례나 지구단위계획 지침상 제한 수치를 직접 입력하여 검토 규모를 강제 보정할 수 있습니다.")

    override_far_active = st.checkbox(
        "지자체 조례/지구단위계획 용적률 직접 제한 (직접 입력)",
        value=st.session_state.get("override_far_active", False),
        help="체크 시 특정 조례(예: 인천시 조례 일반상업 700% 제한) 또는 지구단위계획 지침 수치를 직접 입력하여 앱 전체 규모를 재산정합니다."
    )

    custom_far = None
    if override_far_active:
        override_far_input = st.number_input(
            "지자체 조례/지구단위계획 용적률 상한 (FAR %)",
            min_value=50.0,
            max_value=2500.0,
            value=float(st.session_state.get("override_far_input", 700.0)),
            step=10.0,
            format="%.1f",
            help="예: 인천시 조례 일반상업 주상복합 700.0% 등"
        )
        st.session_state["override_far_active"] = True
        st.session_state["override_far_input"] = override_far_input
        custom_far = override_far_input
        st.caption(f"↳ 지정값 **{custom_far:.0f}%**가 국토계획법 상한과 비교되어 더 엄격한 수치로 자동 적용됩니다.")
    else:
        st.session_state["override_far_active"] = False

    override_bcr_active = st.checkbox(
        "지자체 조례/지구단위계획 건폐율 직접 제한 (직접 입력)",
        value=st.session_state.get("override_bcr_active", False),
        help="체크 시 특정 조례나 지구단위계획 건폐율 수치를 직접 입력합니다."
    )

    custom_bcr = None
    if override_bcr_active:
        override_bcr_input = st.number_input(
            "지자체 조례/지구단위계획 건폐율 상한 (BCR %)",
            min_value=10.0,
            max_value=95.0,
            value=float(st.session_state.get("override_bcr_input", 60.0)),
            step=5.0,
            format="%.1f"
        )
        st.session_state["override_bcr_active"] = True
        st.session_state["override_bcr_input"] = override_bcr_input
        custom_bcr = override_bcr_input
        st.caption(f"↳ 지정값 **{custom_bcr:.0f}%**가 건폐율 실질 기준으로 적용됩니다.")
    else:
        st.session_state["override_bcr_active"] = False

    st.divider()
    st.markdown("#### ⚙️ 시스템 실시간 연동 현황")
    st.markdown("- 🌐 **V-World API 2.0**: PNU / 용도지역 / 지적특성 연동")
    st.markdown("- ⚖️ **법제처 Open API**: 자치조례·부칙 실시간 연동")
    st.caption("엔터프라이즈 기획설계 분석 엔진 v2.5")

    # 사이드바 즉시 다운로드 섹션
    if "exec_analysis" in st.session_state:
        st.markdown("---")
        st.markdown("#### 📥 보고서 즉시 다운로드")
        sb_analysis = st.session_state["exec_analysis"]
        sb_file_base = sb_analysis.get("site", {}).get("refined_address", "site").replace(" ", "_")
        sb_excel = generate_excel_report(sb_analysis).getvalue()
        sb_docx = generate_docx_report(sb_analysis).getvalue()

        st.download_button(
            label="📊 엑셀 분석표 (.xlsx)",
            data=sb_excel,
            file_name=f"건축법규_사업성검토_{sb_file_base}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="sb_dl_excel",
            help="대지개요, 법규비교, 세대구성, 주차산정, 4대심의, 지구단위계획 4개 시트 포함"
        )
        st.download_button(
            label="📑 한글·워드 보고서 (.docx)",
            data=sb_docx,
            file_name=f"건축법규_사업성검토보고서_{sb_file_base}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True,
            key="sb_dl_docx",
            help="한글(HWP 2014 이상) 및 Word에서 서식 깨짐 없이 바로 열람·편집 가능한 정규 문서"
        )
        st.caption("※ HWP(한컴오피스) 및 Word 완벽 호환")

# -------------------------------------------------------------
# 메인 헤더
# -------------------------------------------------------------
st.markdown("""
<div>
    <span class="report-badge">EXECUTIVE FEASIBILITY REPORT</span>
    <span class="report-badge" style="background:#2563EB;">AI ARCHITECTURAL AGENT</span>
    <span class="report-badge" style="background:#059669;">CADASTRAL VERIFIED</span>
</div>
<div class="exec-title">🏛️ 건축 법규 및 사업성 통합 검토 리포트</div>
<div class="exec-sub">대지 위치 및 계획 용도 기반 자치조례 실시간 연동 · 토지대장 면적 검증 · 세대구성 시뮬레이션 및 4대 심의 리스크 종합 진단</div>
""", unsafe_allow_html=True)

# 빠른 프리셋 버튼
col_p1, col_p2, col_p3, col_p4 = st.columns(4)
if col_p1.button("📍 인천 신흥동3가 7-236", use_container_width=True):
        st.session_state["target_addr"] = "인천광역시 제물포구 신흥동3가 7-236"
        
        # 1. 토지대장 기본 정보(지목 등)를 가져옵니다.
        cad_info = vworld.get_official_cadastral_info("2811013000100070236")
        st.session_state["cadastral_info"] = cad_info
        
        # 2. 토지이음 기준 진짜 대지면적을 강제로 세팅합니다. (방해되는 기존 if 코드는 삭제)
        st.session_state["site_area_sqm_val"] = 13236.0
        
        st.rerun()

if col_p2.button("📍 천안 불당동 1479-1", use_container_width=True):
    st.session_state["target_addr"] = "충청남도 천안시 서북구 불당동 1479-1"
    
    cad_info = vworld.get_official_cadastral_info("4413311700114790001")
    st.session_state["cadastral_info"] = cad_info
    
    st.session_state["site_area_sqm_val"] = 8556.7
        
    st.rerun()

if col_p3.button("📍 인천 남동구 구월동 1456", use_container_width=True, help="일반상업지역: 국토계획법 1300% vs 인천조례 700% 이중 검토"):
    st.session_state["target_addr"] = "인천시 남동구 구월동 1456"
    st.session_state["site_area_sqm_val"] = 2854.0
    st.session_state["cadastral_info"] = vworld.get_official_cadastral_info("2820010100114560000")
    st.rerun()

if col_p4.button("📍 부산 해운대구 우동 1408", use_container_width=True):
    st.session_state["target_addr"] = "부산광역시 해운대구 우동 1408"
    st.session_state["site_area_sqm_val"] = 36918.8
    st.session_state["cadastral_info"] = vworld.get_official_cadastral_info("2635010500114080000")
    st.rerun()

# 주소 입력창 및 면적 자동 조회 기능
default_addr = st.session_state.get("target_addr", "서울시 성북구 길음동 1284")

col_addr, col_btn = st.columns([3, 1])
with col_addr:
    addr_input = st.text_input(
        "검토 대상 대지 위치 (도로명 또는 지번 주소)",
        value=default_addr,
        placeholder="예: 서울시 성북구 길음동 1284 또는 강남대로 390",
        label_visibility="collapsed"
    )
with col_btn:
    if st.button("🔍 주소로 면적 자동 조회", use_container_width=True):
        if addr_input:
            st.session_state["target_addr"] = addr_input
            try:
                # 1. 주소로 PNU 코드를 찾습니다.
                pnu_code = vworld.get_pnu_from_address(addr_input)
                
                if pnu_code:
                    # 2. PNU 코드로 토지대장 정보를 가져옵니다.
                    cadastral_info = vworld.get_official_cadastral_info(pnu_code)
                    
                    if cadastral_info and cadastral_info.get("has_cadastral"):
                        # 3. 면적 정보를 세션 상태에 저장합니다.
                        st.session_state["site_area_sqm_val"] = cadastral_info.get("official_area_sqm", 0.0)
                        st.session_state["cadastral_info"] = cadastral_info
                        st.success(f"면적({st.session_state['site_area_sqm_val']}㎡)을 성공적으로 불러왔습니다.")
                        st.rerun() # 화면을 새로고침하여 좌측 사이드바에 면적을 즉시 반영합니다.
                    else:
                        st.warning("해당 주소의 토지대장 정보를 찾을 수 없습니다.")
                else:
                    st.warning("해당 주소의 고유번호(PNU)를 찾을 수 없습니다. 주소를 다시 확인해주세요.")
            except Exception as e:
                st.error("면적 데이터를 불러오는 중 오류가 발생했습니다.")
        else:
            st.warning("주소를 입력해주세요.")

# 상태 업데이트 (버튼을 누르지 않고 주소만 타이핑했을 때를 대비)
if addr_input != st.session_state.get("target_addr"):
    st.session_state["target_addr"] = addr_input

st.write("<div style='height:15px;'></div>", unsafe_allow_html=True) # 여백 추가

btn_col, _ = st.columns([1.3, 3.7])
trigger_analysis = btn_col.button("🚀 통합 법규 및 사업성 정밀 검토 실행", type="primary", use_container_width=True)

# -------------------------------------------------------------
# 데이터 분석 파이프라인
# -------------------------------------------------------------
if trigger_analysis or "exec_analysis" in st.session_state:
    if trigger_analysis:
        with st.spinner("브이월드 및 법제처 Open API 연동하여 대지 분석, 토지대장 검증 및 법규 매트릭스 도출 중..."):
            site_info = vworld.geocode(addr_input)
            if not site_info.get("success"):
                st.error(f"❌ 주소 확인 실패: {site_info.get('error')}")
                st.stop()
            
            x, y = site_info["x"], site_info["y"]
            pnu = site_info.get("pnu", "")
            
            # 토지대장 공부상 면적 및 토지특성 조회
            cadastral_info = vworld.get_official_cadastral_info(pnu)
            st.session_state["cadastral_info"] = cadastral_info
            
            land_info = vworld.get_land_use_and_restrictions(x, y)
            sido, sigg = site_info.get("sido", ""), site_info.get("sigg", "")
            ordin_bundle = moleg.get_municipal_ordinance_bundle(sido, sigg)
            
            analysis = engine.analyze(
                site_info=site_info,
                land_info=land_info,
                ordin_bundle=ordin_bundle,
                site_area=site_area_sqm,
                planned_usage=planned_usage,
                unit_count=unit_count,
                unit_area=unit_area,
                unit_breakdown=unit_breakdown,
                is_units_undetermined=is_units_undetermined,
                cadastral_info=cadastral_info,
                override_far=custom_far,
                override_bcr=custom_bcr
            )
            st.session_state["exec_analysis"] = analysis
            st.session_state["exec_bundle"] = ordin_bundle
            st.session_state["exec_site"] = site_info
            st.session_state["exec_land"] = land_info
    else:
        # 계획 조건 변경 시 실시간 재계산
        site_info = st.session_state["exec_site"]
        land_info = st.session_state["exec_land"]
        ordin_bundle = st.session_state["exec_bundle"]
        cadastral_info = st.session_state.get("cadastral_info", {})

        analysis = engine.analyze(
            site_info=site_info,
            land_info=land_info,
            ordin_bundle=ordin_bundle,
            site_area=site_area_sqm,
            planned_usage=planned_usage,
            unit_count=unit_count,
            unit_area=unit_area,
            unit_breakdown=unit_breakdown,
            is_units_undetermined=is_units_undetermined,
            cadastral_info=cadastral_info,
            override_far=custom_far,
            override_bcr=custom_bcr
        )
        st.session_state["exec_analysis"] = analysis

    site = analysis["site"]
    land = analysis["land"]
    bcr = analysis["bcr"]
    far = analysis["far"]
    feas = analysis["feasibility"]
    height = analysis["height"]
    delibs = analysis["deliberations"]
    constraints = analysis["design_constraints"]
    special = analysis["special_ordinance"]
    dp_alert = analysis["district_plan_alert"]
    three_lines = analysis["executive_summary_3lines"]
    area_val = analysis["area_validation"]
    parking_info = constraints["parking"]

    st.markdown("---")

    # 지구단위계획 / 재개발 경고 배너
    if dp_alert["required"]:
        st.markdown(f"""
        <div class="warning-alert">
            <h4 style="margin:0 0 6px 0; font-size:1.05rem; font-weight:800;">⚠️ [필독] {dp_alert['title']}</h4>
            <div style="font-size:0.92rem; line-height:1.6;">
                {dp_alert['message']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # [상단 Header & Executive Summary] 4대 핵심 지표 카드
    # ---------------------------------------------------------
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="metric-box green">
            <div class="metric-header">① 적용 건폐율 (BCR)</div>
            <div class="metric-value-lg">{bcr.get('applied_limit')} <span style="font-size:0.85rem; color:#64748B; font-weight:600;">(적용 기준)</span></div>
            <div style="font-size:0.75rem; color:#059669; margin-top:4px; font-weight:700; line-height:1.4;">{bcr.get('comparison_summary')}</div>
            <div class="metric-footnote">최대 건축면적: <b>{feas['max_building_area_sqm']:,.0f}㎡ ({feas['max_building_area_py']:,.0f}평)</b></div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="metric-box purple">
            <div class="metric-header">② 적용 용적률 (FAR)</div>
            <div class="metric-value-lg">{far.get('applied_limit')} <span style="font-size:0.85rem; color:#64748B; font-weight:600;">(엄격 기준 적용)</span></div>
            <div style="font-size:0.75rem; color:#7C3AED; margin-top:4px; font-weight:700; line-height:1.4;">{far.get('comparison_summary')}</div>
            <div class="metric-footnote">지상 연면적: <b>{feas['max_ground_gfa_sqm']:,.0f}㎡ ({feas['max_ground_gfa_py']:,.0f}평)</b></div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="metric-box orange">
            <div class="metric-header">③ 예상 최고높이 / 층수</div>
            <div class="metric-value-lg">지상 {feas['est_floors']}층 <span style="font-size:1.1rem; color:#64748B;">({feas['est_height_m']}m)</span></div>
            <div class="metric-footnote">층고 가정: <b>층당 {feas['floor_height_m']}m</b> / 일조사선 셋백</div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        risk_sum = delibs["risk_summary"]
        risk_box_cls = "red" if risk_sum["high_risk_count"] >= 2 else "orange"
        st.markdown(f"""
        <div class="metric-box {risk_box_cls}">
            <div class="metric-header">④ 주요 심의 리스크 요약</div>
            <div class="metric-value-lg" style="color: {'#EF4444' if risk_sum['high_risk_count']>=2 else '#F59E0B'};">
                {risk_sum['high_risk_count']}개 대상
            </div>
            <div class="metric-footnote">인허가 소요: <b>{risk_sum['total_timeline_est']}</b></div>
        </div>
        """, unsafe_allow_html=True)

    # 3줄 요약 결론 박스
    st.markdown(f"""
    <div class="conclusion-box">
        <h4>💡 보고용 3줄 핵심 결론 (Executive Summary)</h4>
        <div class="conclusion-item">{three_lines[0]}</div>
        <div class="conclusion-item">{three_lines[1]}</div>
        <div class="conclusion-item">{three_lines[2]}</div>
    </div>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 보고용 즉시 다운로드 Quick Action Bar
    # ---------------------------------------------------------
    file_base = site.get("refined_address", "site").replace(" ", "_")
    excel_bytes = generate_excel_report(analysis).getvalue()
    docx_bytes = generate_docx_report(analysis).getvalue()
    md_text = generate_markdown_report(analysis)

    st.markdown("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span style="font-weight:700; color:#1E293B; font-size:0.95rem;">📥 보고용 파일 원클릭 다운로드:</span>
        <span style="font-size:0.8rem; color:#64748B;">엑셀(.xlsx) / 한글·워드(.docx) / 마크다운(.md)</span>
    </div>
    """, unsafe_allow_html=True)

    dl_q1, dl_q2, dl_q3 = st.columns(3)
    with dl_q1:
        st.download_button(
            "📊 [실무용] 엑셀 상세 분석표 (.xlsx)",
            data=excel_bytes,
            file_name=f"건축법규_사업성검토_{file_base}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True,
            help="대지개요, 법정vs조례비교, 세대구성/주차산정, 4대심의, 지구단위계획 4개 시트 포함",
            key="quick_dl_excel"
        )
    with dl_q2:
        st.download_button(
            "📑 [보고용] 한글·워드 보고서 (.docx)",
            data=docx_bytes,
            file_name=f"건축법규_사업성검토보고서_{file_base}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True,
            help="한컴오피스(한글 HWP 2014 이상) 및 MS Word에서 서식 깨짐 없이 바로 열람·편집 가능한 정규 문서",
            key="quick_dl_docx"
        )
    with dl_q3:
        st.download_button(
            "📄 [요약용] 마크다운 보고서 (.md)",
            data=md_text,
            file_name=f"건축법규_사업성검토보고서_{file_base}.md",
            mime="text/markdown",
            type="secondary",
            use_container_width=True,
            help="협업툴(Notion, GitHub) 연동용 마크다운 요약",
            key="quick_dl_md"
        )
    st.write("")

    # ---------------------------------------------------------
    # 5대 전문 탭 (Tabs)
    # ---------------------------------------------------------
    t1, t2, t3, t4, t5 = st.tabs([
        "탭 1. 대지 및 법정 규제 개요",
        "탭 2. 용도별 설계 제약 및 주차 산정",
        "탭 3. 4대 주요 심의 판정 및 절차",
        "탭 4. 지구단위계획 및 지자체 특별 조례",
        "탭 5. 한 줄 사업성 / 리스크 체크리스트"
    ])

    # ---------------------------------------------------------
    # 탭 1. 대지 및 법정 규제 개요
    # ---------------------------------------------------------
    with t1:
        st.markdown('<div class="section-title">📍 대지 지적 속성 및 공간정보 (PNU 기준)</div>', unsafe_allow_html=True)
        col_prop1, col_prop2 = st.columns([1.4, 1.1])
        with col_prop1:
            prop_data = {
                "구분 항목": ["정제 지번 주소", "필지고유번호 (PNU)", "법정 용도지역", "행정구역 체계", "지구단위계획구역 여부", "기타 중첩 용도지구/구역"],
                "속성 상세 내역": [
                    site.get("refined_address"),
                    site.get("pnu"),
                    land.get("primary_zoning"),
                    f"{site.get('sido')} {site.get('sigg')} {site.get('emd')}",
                    f"포함됨 ({', '.join(land.get('district_plan_names', []))})" if land.get("is_district_plan") else "해당없음 (일반 조례 적용)",
                    ", ".join(land.get("overlay_zones", []) + land.get("restrictions", [])) or "특이 규제구역 없음"
                ]
            }
            st.dataframe(pd.DataFrame(prop_data), hide_index=True, use_container_width=True)

        with col_prop2:
            st.markdown(f"""
            <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:16px; border-radius:8px;">
                <div style="font-size:0.85rem; color:#64748B; font-weight:700;">대지 검토 면적</div>
                <div style="font-size:1.6rem; font-weight:800; color:#0F172A; margin:4px 0;">{site_area_sqm:,.1f} ㎡</div>
                <div style="font-size:0.95rem; color:#2563EB; font-weight:700;">약 {site_area_py:,.1f} 평</div>
                <div style="margin-top:10px; font-size:0.8rem; color:#64748B;">
                    경위도 좌표: <code>{site.get('x',0.0):.6f}, {site.get('y',0.0):.6f}</code>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 🌟 대지면적 검증 및 토지대장 상세 특성 블록
        st.markdown('<div class="section-title">📐 토지대장 대지면적 검증 및 토지특성 (브이월드 연동)</div>', unsafe_allow_html=True)
        if area_val.get("has_cadastral"):
            off_sqm = area_val.get("official_area_sqm", 0.0)
            off_py = area_val.get("official_area_py", 0.0)
            diff_sqm = area_val.get("diff_sqm", 0.0)
            diff_pct = area_val.get("diff_pct", 0.0)
            is_match = area_val.get("is_match", True)

            col_val_t, col_val_btn = st.columns([2.5, 1])
            with col_val_t:
                val_table = [
                    {
                        "구분": "토지대장 공부상 면적",
                        "면적(㎡)": f"{off_sqm:,.1f} ㎡",
                        "평형 환산": f"약 {off_py:,.1f} 평",
                        "상태": "기준 (원천 데이터)"
                    },
                    {
                        "구분": "현재 계획 입력 면적",
                        "면적(㎡)": f"{site_area_sqm:,.1f} ㎡",
                        "평형 환산": f"약 {site_area_py:,.1f} 평",
                        "상태": "일치 (정상)" if is_match else f"⚠️ 편차 {diff_sqm:,.1f}㎡ ({diff_pct}%)"
                    }
                ]
                st.dataframe(pd.DataFrame(val_table), hide_index=True, use_container_width=True)

            with col_val_btn:
                if not is_match:
                    st.warning(f"⚠️ 공부상 면적과 **{diff_sqm:,.1f}㎡** 편차가 있습니다.")
                    if st.button(f"📥 공부상 면적 적용 ({off_sqm:,.1f}㎡)", key="tab1_apply_area", use_container_width=True, type="primary"):
                        st.session_state["site_area_sqm_val"] = float(off_sqm)
                        st.rerun()
                else:
                    st.success("✅ 계획 면적이 토지대장 공부상 면적과 정확히 일치합니다.")

            # 토지특성 상세
            col_c1, col_c2, col_c3, col_c4 = st.columns(4)
            col_c1.metric("지목", area_val.get("jimok", "대"))
            col_c2.metric("개별공시지가", area_val.get("official_price", "미공시"))
            col_c3.metric("도로접면", area_val.get("road_side", "중로각지"))
            col_c4.metric("지세 및 형상", f"{area_val.get('topography_height','평지')} / {cadastral_info.get('topography_shape','부정형')}")
        else:
            st.info("ℹ️ 해당 필지의 토지대장 세부 특성을 조회할 수 없습니다. (수동 입력 면적 적용 중)")

        st.markdown('<div class="section-title">⚖️ 법정 vs 지자체 조례/지구단위계획 제한 이중 비교표</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:#EFF6FF; border:1px solid #BFDBFE; border-left:5px solid #2563EB; padding:12px 16px; border-radius:6px; margin-bottom:12px;">
            <div style="font-weight:700; color:#1E40AF; font-size:0.95rem;">⚖️ [법정 기준 vs 조례·지구단위계획 상한 이중 검토 판정 결과]</div>
            <div style="font-size:0.92rem; color:#1E293B; margin-top:6px; line-height:1.6;">
                • <b>용적률 (FAR)</b>: <span style="color:#2563EB; font-weight:700;">{far.get('comparison_summary')}</span><br/>
                • <b>건폐율 (BCR)</b>: <span style="color:#059669; font-weight:700;">{bcr.get('comparison_summary')}</span>
            </div>
            <div style="font-size:0.8rem; color:#64748B; margin-top:6px;">
                ※ 국토계획법상 법정 상한과 관할 지자체 조례 및 지구단위계획 지침 상한 중 <b>더 엄격한(낮은) 기준</b>이 실질적인 사업성 검토 기준으로 자동 적용되었습니다.
            </div>
        </div>
        """, unsafe_allow_html=True)

        comp_data = [
            {
                "규제 항목": "건폐율 (BCR)",
                "국토계획법 법정 상한": bcr.get("national_limit"),
                "지자체 조례/지침 상한": bcr.get("ordinance_limit"),
                "★ 최종 적용 기준치 (엄격 기준)": f"★ {bcr.get('applied_limit')}",
                "이중 비교 판정 요약": bcr.get("comparison_summary"),
                "근거 법규 및 조례": bcr.get("law_source"),
                "비고 및 세부 조건": bcr.get("notes")
            },
            {
                "규제 항목": "용적률 (FAR)",
                "국토계획법 법정 상한": far.get("national_limit"),
                "지자체 조례/지침 상한": far.get("ordinance_limit"),
                "★ 최종 적용 기준치 (엄격 기준)": f"★ {far.get('applied_limit')}",
                "이중 비교 판정 요약": far.get("comparison_summary"),
                "근거 법규 및 조례": far.get("law_source"),
                "비고 및 세부 조건": far.get("notes")
            },
            {
                "규제 항목": "최고높이 / 층수",
                "국토계획법 법정 상한": "건축법 제60조 / 제61조",
                "지자체 조례/지침 상한": height.get("summary_limit"),
                "★ 최종 적용 기준치 (엄격 기준)": f"지상 {feas['est_floors']}층 ({feas['est_height_m']}m)",
                "이중 비교 판정 요약": "가로구역별 고시높이 및 정북사선 셋백 동시 충족",
                "근거 법규 및 조례": f"{site.get('sido')} 건축조례 제33조·제35조",
                "비고 및 세부 조건": "가로구역별 고시높이 및 정북방향 일조사선 이격(10m이하 1.5m, 10m초과 1/2) 동시 충족"
            }
        ]
        st.dataframe(pd.DataFrame(comp_data), hide_index=True, use_container_width=True)

        st.markdown('<div class="section-title">🎁 용적률 완화 및 인센티브 가능 항목 (기부채납·친환경)</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(analysis["incentives"]), hide_index=True, use_container_width=True)

    # ---------------------------------------------------------
    # 탭 2. 용도별 설계 제약 및 주차 산정
    # ---------------------------------------------------------
    with t2:
        st.markdown(f'<div class="section-title">🏢 [{planned_usage}] 계획 설계 필수 규정 및 제약 조건</div>', unsafe_allow_html=True)
        for rule in constraints["usage_rules"]:
            st.markdown(f"- 📌 **{rule}**")

        # 세대 구성 현황 표 (미정 모드 또는 상세 세대 구성 반영)
        st.markdown('<div class="section-title">🏘️ 세대 및 호실 구성 시뮬레이션 결과</div>', unsafe_allow_html=True)
        if feas.get("is_undetermined"):
            st.info(
                f"💡 **세대 구성 미정 (자동 추정 모드 적용 중)**\n"
                f"- 총 산정 세대수: **{feas.get('effective_unit_count')} 세대/호** (아파트 {feas.get('effective_apt_count')}세대 + 오피스텔 {feas.get('effective_off_count')}호)\n"
                f"- 세대당 평균 전용면적: **약 {feas.get('effective_unit_area')} ㎡**"
            )
        
        breakdown = feas.get("unit_breakdown", {})
        if breakdown:
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if breakdown.get("apt"):
                    st.markdown("**[공동주택 평형별 구성]**")
                    apt_df = pd.DataFrame([
                        {"평형 타입": f"{k} 타입", "세대수": f"{v} 세대", "전용면적(평)": f"약 {round(float(k)/3.305785, 1)}평"}
                        for k, v in breakdown["apt"].items() if v > 0
                    ])
                    st.dataframe(apt_df, hide_index=True, use_container_width=True)
            with col_b2:
                if breakdown.get("officetel"):
                    st.markdown("**[오피스텔 평형별 구성]**")
                    off_df = pd.DataFrame([
                        {"평형 타입": f"{k} 타입", "호실수": f"{v} 호", "전용면적(평)": f"약 {round(float(k)/3.305785, 1)}평"}
                        for k, v in breakdown["officetel"].items() if v > 0
                    ])
                    st.dataframe(off_df, hide_index=True, use_container_width=True)

        st.markdown('<div class="section-title">📐 사선제한 및 대지 안의 공지 (이격거리)</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(constraints["setback_rules"]), hide_index=True, use_container_width=True)

        st.markdown('<div class="section-title">🅿️ 법정 및 지자체 조례 기준 주차대수 자동 산정</div>', unsafe_allow_html=True)
        p_c1, p_c2, p_c3, p_c4 = st.columns(4)
        with p_c1:
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1px solid #CBD5E1; padding:14px; border-radius:8px; text-align:center;">
                <div style="font-size:0.8rem; color:#64748B;">법정 최소 주차대수</div>
                <div style="font-size:1.6rem; font-weight:800; color:#0F172A;">{parking_info['legal_count']} 대</div>
                <div style="font-size:0.75rem; color:#64748B;">주차장법 시행령 기준</div>
            </div>
            """, unsafe_allow_html=True)
        with p_c2:
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1px solid #CBD5E1; padding:14px; border-radius:8px; text-align:center;">
                <div style="font-size:0.8rem; color:#64748B;">지자체 조례 기준</div>
                <div style="font-size:1.6rem; font-weight:800; color:#2563EB;">{parking_info['ordinance_count']} 대</div>
                <div style="font-size:0.75rem; color:#64748B;">{site.get('sido')} 주차장 조례</div>
            </div>
            """, unsafe_allow_html=True)
        with p_c3:
            st.markdown(f"""
            <div style="background:#FFFFFF; border:2px solid #10B981; padding:14px; border-radius:8px; text-align:center;">
                <div style="font-size:0.8rem; color:#059669; font-weight:700;">★ 실무 권장 주차대수</div>
                <div style="font-size:1.6rem; font-weight:800; color:#059669;">{parking_info['recommended_count']} 대</div>
                <div style="font-size:0.75rem; color:#059669;">분양성 및 심의권고 반영</div>
            </div>
            """, unsafe_allow_html=True)
        with p_c4:
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1px solid #CBD5E1; padding:14px; border-radius:8px; text-align:center;">
                <div style="font-size:0.8rem; color:#64748B;">친환경차 충전시설</div>
                <div style="font-size:1.6rem; font-weight:800; color:#7C3AED;">{parking_info['ev_charging_count']} 대</div>
                <div style="font-size:0.75rem; color:#64748B;">법정 5% 이상 의무화</div>
            </div>
            """, unsafe_allow_html=True)

        st.caption(f"ℹ️ **산정 세부 근거**: {parking_info['basis']} (장애인 전용 주차구획 {parking_info['accessibility_count']}대 별도)")

    # ---------------------------------------------------------
    # 탭 3. 8대 주요 심의 및 평가 자동 판정 (O/X) 및 리스크 매트릭스
    # ---------------------------------------------------------
    with t3:
        st.markdown('<div class="section-title">🛡️ 8대 주요 심의 및 영향평가 자동 판정 (O/X)</div>', unsafe_allow_html=True)
        st.caption("대지면적 및 실무 기준을 바탕으로 추정한 결과입니다. (실제 토지이용계획확인원 확인 필수)")

        # 기존 4대 심의 테이블 표시 (HTML 렌더링으로 컬러 태그 적용)
        delib_rows = []
        for d in delibs["items"]:
            tag_class = "tag-red" if d["tag"] == "규제" else ("tag-yellow" if d["tag"] == "주의" else "tag-green")
            delib_rows.append({
                "심의/평가 명칭": d["name"],
                "대상 여부": d["required"],
                "리스크 등급": f"<span class='{tag_class}'>{d['tag']}</span>",
                "예상 소요기간": d["timeline"],
                "주관기관": d["authority"],
                "필수 체크포인트": d["checkpoints"]
            })
        
        df_delib = pd.DataFrame(delib_rows)
        st.write(df_delib.to_html(escape=False, index=False), unsafe_allow_html=True)

        st.write("")
        st.markdown('<div class="section-title">🌍 4대 영향평가 (환경/교육/지하/문화재) 추가 진단</div>', unsafe_allow_html=True)
        
        # 현재 면적 및 세대수 가져오기
        current_area = float(st.session_state.get("site_area_sqm_val", 0.0))
        current_units = feas.get("effective_unit_count", 0)

        col_sim1, col_sim2 = st.columns(2)

        with col_sim1:
            # 1. 환경영향평가
            st.markdown("#### 1️⃣ 환경영향평가 (소규모 포함)")
            if current_area >= 100000:
                st.error(f"🚨 대지면적 {current_area:,.0f}㎡: **환경영향평가 대상** 가능성이 매우 높습니다 (통상 10만㎡ 이상). 심의 기간을 길게 잡아야 합니다.")
            elif current_area >= 5000:
                st.warning(f"⚠️ 대지면적 {current_area:,.0f}㎡: 용도지역(보전관리지역 등)에 따라 **소규모 환경영향평가** 대상일 수 있습니다.")
            else:
                st.success(f"✅ 대지면적 {current_area:,.0f}㎡: 일반적인 환경영향평가 면적 기준(5,000㎡) 미만으로 대상이 아닐 확률이 높습니다.")

            # 2. 교육환경평가
            st.markdown("#### 2️⃣ 교육환경평가")
            if current_area >= 100000 or (isinstance(current_units, int) and current_units >= 1000):
                 st.error(f"🚨 대규모(연면적 10만㎡ 또는 21층 이상) 건축물이거나 반경 200m 내 학교가 있을 경우 **필수 대상**입니다. 관할 교육청 확인이 시급합니다.")
            else:
                 st.info("💡 사업지 반경 200m 이내에 학교(예정지 포함)가 있어 **'교육환경보호구역'**에 속할 경우 심의 대상입니다. (토지이용계획확인원 확인 필요)")

        with col_sim2:
            # 3. 지하안전평가
            st.markdown("#### 3️⃣ 지하안전평가")
            st.warning("⚠️ **굴착 깊이에 따른 평가 기준 (건축도면 확인 필수)**\n- **10m 이상 20m 미만** (약 지하 3~5층): 소규모 지하안전평가\n- **20m 이상** (약 지하 6층 이상): 지하안전평가 필수")

            # 4. 문화재 보존영향 검토
            st.markdown("#### 4️⃣ 문화재 보존영향 검토")
            st.info("💡 사업지가 **'역사문화환경 보존지역'** (일반적으로 지정문화재 경계로부터 반경 500m 이내)에 포함될 경우, 지자체 문화재 위원회의 층수 및 디자인 심의를 통과해야 합니다.")

        st.write("")
        st.markdown('<div class="section-title">🚒 피난 / 방화 / 소방 안전 필수 특이사항 매뉴얼</div>', unsafe_allow_html=True)
        for note in delibs["fire_safety_notes"]:
            st.markdown(f"- {note}")

        with st.expander("📑 심의별 필수 제출 도서 목록 상세 확인"):
            for d in delibs["items"]:
                st.markdown(f"**[{d['name']}]**")
                st.markdown(f"- 제출 도서: `{d['docs']}`")
                st.markdown(f"- 관계 법령: {d['law']}")

    # ---------------------------------------------------------
    # 탭 4. 지구단위계획 및 지자체 특별 조례
    # ---------------------------------------------------------
    with t4:
        st.markdown(f'<div class="section-title">🏛️ {site.get("sido")} 건축 조례 및 특별 규정 하이라이트</div>', unsafe_allow_html=True)
        for sh in special["special_highlights"]:
            st.markdown(f"- {sh}")

        # 🌟 지구단위계획 상세 지침 6대 핵심 체크리스트 표 (실무 요구사항 반영)
        st.markdown('<div class="section-title">📋 지구단위계획 지침 상세 실무 체크리스트 (6대 핵심 항목 표)</div>', unsafe_allow_html=True)
        st.markdown("""
        > 💡 **실무 지침 유의사항**: 지구단위계획구역은 일반 조례보다 지구단위계획 수립 지침이 우선합니다.  
        > 아래 6대 핵심 기준을 착수 단계에서 사전 검토하여 기획설계 및 사업수지표에 반영해야 합니다.
        """)

        checklist_items = special.get("district_plan_checklist", [])
        if checklist_items:
            df_check = pd.DataFrame(checklist_items)
            st.dataframe(df_check, hide_index=True, use_container_width=True)

            # 항목별 심층 설계 실무 가이드 Expander
            with st.expander("🔍 6대 지침별 심층 설계 착안사항 상세 펼치기"):
                for c in checklist_items:
                    st.markdown(f"#### 📌 {c['카테고리']} - {c['세부 규정 항목']}")
                    st.markdown(f"- **법적/지침 기준**: {c['법적 및 지침 기준']}")
                    st.markdown(f"- **실무 설계 착안사항**: `{c['실무 설계 점검사항']}`")
                    st.markdown(f"- **인센티브 및 완화**: 🎁 {c['완화 및 인센티브']}")
                    st.markdown("---")

        st.markdown('<div class="section-title">📜 법제처 Open API 실시간 조례 원문 열람</div>', unsafe_allow_html=True)
        plan_ord = ordin_bundle.get("planning_ordinance")
        bld_ord = ordin_bundle.get("building_ordinance")

        co1, co2 = st.columns(2)
        with co1:
            if plan_ord:
                st.success(f"**도시계획조례**: {plan_ord.get('title')} ({plan_ord.get('org')})")
                with st.expander("도시계획조례 건폐율/용적률 조문 보기"):
                    for a in ordin_bundle.get("bcr_articles", []) + ordin_bundle.get("far_articles", []):
                        st.markdown(f"**제{a.get('num')}조 ({a.get('title')})**")
                        st.text(a.get("content"))
        with co2:
            if bld_ord:
                st.success(f"**건축조례**: {bld_ord.get('title')} ({bld_ord.get('org')})")
                with st.expander("건축조례 최고높이/심의 조문 보기"):
                    for a in ordin_bundle.get("height_articles", []) + ordin_bundle.get("deliberation_articles", []):
                        st.markdown(f"**제{a.get('num')}조 ({a.get('title')})**")
                        st.text(a.get("content"))

    # ---------------------------------------------------------
    # 탭 5. 한 줄 사업성 / 리스크 체크리스트 (보고서용)
    # ---------------------------------------------------------
    with t5:
        st.markdown('<div class="section-title">📊 임원진 보고용 사업성 개략 볼륨 및 건축 개요표</div>', unsafe_allow_html=True)

        vol_table = [
            {"사업성 지표": "대지 면적", "산출 면적 (㎡)": f"{site_area_sqm:,.1f} ㎡", "평형 환산 (평)": f"{site_area_py:,.1f} 평", "비고": "토지대장 검증 기준"},
            {"사업성 지표": "최대 건축면적", "산출 면적 (㎡)": f"{feas['max_building_area_sqm']:,.1f} ㎡", "평형 환산 (평)": f"{feas['max_building_area_py']:,.1f} 평", "비고": f"적용 건폐율 {bcr.get('applied_limit')} ({bcr.get('comparison_summary')})"},
            {"사업성 지표": "지상 연면적 (기본)", "산출 면적 (㎡)": f"{feas['max_ground_gfa_sqm']:,.1f} ㎡", "평형 환산 (평)": f"{feas['max_ground_gfa_py']:,.1f} 평", "비고": f"적용 용적률 {far.get('applied_limit')} ({far.get('comparison_summary')})"},
            {"사업성 지표": "지상 연면적 (인센티브)", "산출 면적 (㎡)": f"{feas['incentive_ground_gfa_sqm']:,.1f} ㎡", "평형 환산 (평)": f"{feas['incentive_ground_gfa_py']:,.1f} 평", "비고": f"완화 용적률 {feas['incentive_far_pct']}% 적용"},
            {"사업성 지표": "예상 지하층 연면적", "산출 면적 (㎡)": f"{feas['est_basement_gfa_sqm']:,.1f} ㎡", "평형 환산 (평)": f"{round(feas['est_basement_gfa_sqm']/3.305785, 1):,.1f} 평", "비고": "주차장 및 기계실 (지상 대비 45%)"},
            {"사업성 지표": "예상 총 연면적", "산출 면적 (㎡)": f"{feas['est_total_gfa_sqm']:,.1f} ㎡", "평형 환산 (평)": f"{feas['est_total_gfa_py']:,.1f} 평", "비고": "지상 + 지하 합산 연면적"},
            {"사업성 지표": "예상 건물 규모", "산출 면적 (㎡)": f"지상 {feas['est_floors']}층 / 지하 2~3층", "평형 환산 (평)": f"높이 약 {feas['est_height_m']} m", "비고": "가로구역 및 일조사선 셋백 반영"},
            {"사업성 지표": "계획 세대/호실수", "산출 면적 (㎡)": f"{feas['effective_unit_count']} 세대/호", "평형 환산 (평)": f"평균 전용 {feas['effective_unit_area']}㎡", "비고": f"실무권장 주차 {parking_info['recommended_count']}대 확보 필요"}
        ]
        st.dataframe(pd.DataFrame(vol_table), hide_index=True, use_container_width=True)

        st.markdown('<div class="section-title">🚨 착수 전 필수 리스크 체크리스트</div>', unsafe_allow_html=True)
        risk_checklist = [
            ("일조권 사선제한 검토", "정북방향 인접대지의 레벨(고저차) 및 경계선 확인을 위한 현황측량 선행 필수"),
            ("지하 굴토심의 리스크", "지하 2층 이상 굴착 시 안전관리계획서 및 지반조사보고서(시추조사) 조기 착수 필수"),
            ("지구단위계획 지침 준수", "건축선 후퇴(전면공지), 공공보행통로 폭(4~6m) 및 1층 가로활성화 투시벽면율 50% 사전 반영"),
            ("교통영향평가 대상성", "연면적 변경에 따른 교통심의 트리거 규모(2만~3.6만㎡) 도달 여부 모니터링"),
            ("전기차 화재방화 기준", "지하주차장 스프링클러 헤드 간격(2.3m) 및 방화구획 최신 소방지침 반영")
        ]
        for title, desc in risk_checklist:
            st.markdown(f"- ☑️ **{title}**: {desc}")

        st.divider()
        st.markdown('<div class="section-title">📥 보고용 통합 파일 즉시 다운로드</div>', unsafe_allow_html=True)
        st.caption("실무 설계 및 의사결정 보고에 최적화된 3대 포맷(Excel, Word/HWP 호환 서식, Markdown)으로 내보내기를 지원합니다.")

        col_dl1, col_dl2, col_dl3 = st.columns(3)
        with col_dl1:
            st.download_button(
                label="📊 [실무용] 엑셀 상세 분석표 (.xlsx)",
                data=excel_bytes,
                file_name=f"건축법규_사업성검토_{file_base}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
                help="대지개요, 법정vs조례비교, 세대구성/주차산정, 4대심의, 지구단위계획 체크리스트 4개 시트 포함",
                key="tab5_dl_excel"
            )
            st.caption("✓ 4개 전문 시트 서식 완비 (수식/테두리/음영/포맷 적용)")

        with col_dl2:
            st.download_button(
                label="📑 [보고용] 한글·워드 보고서 (.docx)",
                data=docx_bytes,
                file_name=f"건축법규_사업성검토보고서_{file_base}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                use_container_width=True,
                help="한컴오피스(한글 HWP 2014 이상) 및 MS Word에서 서식 깨짐 없이 바로 열람·편집 가능한 정규 보고서",
                key="tab5_dl_docx"
            )
            st.caption("✓ 한글(HWP 2014 이상) 및 Word 완벽 호환 (정규 표/콜아웃)")

        with col_dl3:
            st.download_button(
                label="📄 [요약용] 마크다운 보고서 (.md)",
                data=md_text,
                file_name=f"건축법규_사업성검토보고서_{file_base}.md",
                mime="text/markdown",
                type="secondary",
                use_container_width=True,
                help="Notion, GitHub, Confluence 등 협업툴 붙여넣기 최적화",
                key="tab5_dl_md"
            )
            st.caption("✓ Notion, Confluence 등 협업툴 붙여넣기 최적화")

else:
    st.info("💡 좌측 사이드바에서 [계획 용도]와 [대지 면적]을 확인하신 후 상단의 **[🚀 통합 법규 및 사업성 정밀 검토 실행]** 버튼을 눌러주세요.")
