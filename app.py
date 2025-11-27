
from datetime import datetime, timedelta
import streamlit as st
from streamlit_option_menu import option_menu

DATE_FMT = "%Y-%m-%d"

# 1. 목표 일자 -> 주령 계산 함수
def calculate_age_by_date(hatch_date_str, target_date_str):
    """입추일과 목표일자를 받아 주령(주+일)을 계산합니다."""
    try:
        hatch = datetime.strptime(hatch_date_str, DATE_FMT).date()
        target = datetime.strptime(target_date_str, DATE_FMT).date()
    except ValueError:
        return {"error": "날짜 형식이 올바르지 않습니다."}

    diff = (target - hatch).days

    if diff < 0:
        return {"error": "목표 일자가 입추일보다 빠릅니다."}

    weeks = diff // 7
    extra_days = diff % 7

    return {
        "total_days": diff,
        "weeks": weeks,
        "extra_days": extra_days,
        "hatch_date": hatch_date_str,
        "target_date": target_date_str
    }

# 2. 목표 주령 -> 목표 일자 계산 함수
def calculate_date_by_age(hatch_date_str, target_weeks, target_days):
    """입추일과 목표 주령을 받아 목표 일자를 계산합니다."""
    try:
        hatch = datetime.strptime(hatch_date_str, DATE_FMT)
        tw = int(target_weeks)
        td = int(target_days)
    except ValueError:
        return {"error": "입추일 또는 주령(주/일) 값이 올바르지 않습니다."}

    total_days = tw * 7 + td
    target_date = hatch + timedelta(days=total_days)

    return {
        "target_date": target_date.strftime(DATE_FMT),
        "total_days": total_days,
        "hatch_date": hatch_date_str,
        "target_weeks": tw,
        "target_days": td
    }

# ----------------- Streamlit UI -----------------

st.set_page_config(
    page_title="닭 주령 계산기",
    layout="centered",
    initial_sidebar_state="auto"
)

st.title("🐔 한국양계 주령 계산기 (모바일 웹)")

# 오늘 날짜 기본값 설정
today = datetime.now().date()

# 메뉴 선택 (사이드바가 아닌 메인 화면에 표시)
selected = option_menu(
    menu_title=None,
    options=["일자 → 주령 계산", "주령 → 일자 계산"],
    icons=["calendar-check", "clock"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#0f1115"},
        "icon": {"color": "#5ab3ff", "font-size": "18px"}, 
        "nav-link": {"font-size": "16px", "text-align": "center", "margin":"0px", "--hover-color": "#1c2231"},
        "nav-link-selected": {"background-color": "#5ab3ff", "color": "white"},
    }
)

# ============== 모드 1: 일자 -> 주령 계산 ==============
if selected == "일자 → 주령 계산":
    st.header("1️⃣ 목표 일자 기준 주령 계산")

    with st.form("date_to_week_form"):
        hatch_date = st.date_input("입추일", value=today - timedelta(weeks=10), format="YYYY-MM-DD")
        target_date = st.date_input("목표 일자", value=today, format="YYYY-MM-DD")
        submitted = st.form_submit_button("주령 계산하기", type="primary")

        if submitted:
            result = calculate_age_by_date(str(hatch_date), str(target_date))

            if "error" in result:
                st.error(f"오류: {result['error']}")
            else:
                st.success(f"✅ 계산 완료! ({result['hatch_date']} ~ {result['target_date']})")
                st.metric(
                    label="현재 주령", 
                    value=f"{result['weeks']}주 {result['extra_days']}일", 
                    delta=f"{result['total_days']}일 경과"
                )

# ============== 모드 2: 주령 -> 일자 계산 ==============
elif selected == "주령 → 일자 계산":
    st.header("2️⃣ 목표 주령 기준 일자 계산")

    with st.form("week_to_date_form"):
        hatch_date_2 = st.date_input("입추일", value=today, format="YYYY-MM-DD")
        
        col1, col2 = st.columns(2)
        with col1:
            target_weeks = st.number_input("목표 주령 (주)", min_value=0, max_value=100, value=15)
        with col2:
            target_days = st.number_input("목표 주령 (일)", min_value=0, max_value=6, value=0)

        submitted_2 = st.form_submit_button("목표 일자 계산하기", type="primary")

        if submitted_2:
            result = calculate_date_by_age(str(hatch_date_2), target_weeks, target_days)

            if "error" in result:
                st.error(f"오류: {result['error']}")
            else:
                st.success(f"✅ 계산 완료! (입추일: {result['hatch_date']})")
                st.metric(
                    label=f"목표 ({result['target_weeks']}주 {result['target_days']}일)가 되는 날짜",
                    value=f"{result['target_date']}"
                )
                st.info(f"총 일령: {result['total_days']}일")
                
