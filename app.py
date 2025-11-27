import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu
import json # 1. JSON 모듈 추가

DATE_FMT = "%Y-%m-%d"
DATA_FILE = "flocks_data.json" # 2. 데이터 파일명 정의

# ----------------- 1. 계산 로직 함수 -----------------

def calculate_age(hatch_date, target_date):
    """입추일과 목표일자를 받아 일령 및 주령(주+일)을 계산합니다."""
    diff = (target_date.date() - hatch_date.date()).days
    if diff < 0:
        return diff, "입추 전"
    weeks = diff // 7
    extra_days = diff % 7
    return diff, f"{weeks}주 {extra_days}일"

def calculate_target_date(hatch_date, target_weeks, target_days):
    """입추일과 목표 주령을 받아 목표 일자를 계산합니다."""
    total_days = target_weeks * 7 + target_days
    target_date = hatch_date + timedelta(days=total_days)
    return target_date, total_days

def format_date_with_weekday(d):
    """날짜를 요일과 함께 포맷합니다."""
    wk = ["월", "화", "수", "목", "금", "토", "일"]
    return f"{d.strftime(DATE_FMT)} ({wk[d.weekday()]})"


# ----------------- 2. Streamlit UI 및 관리 로직 -----------------

# [NEW] 데이터 저장 및 불러오기 함수
def load_data():
    """데이터를 파일에서 불러옵니다. (앱 시작 시 호출)"""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data(flocks_data):
    """데이터를 파일에 저장합니다. (데이터 변경 시 호출)"""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(flocks_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        # Streamlit Cloud에서는 쓰기 권한이나 환경 문제로 실패할 수 있습니다.
        pass


# 세션 상태 초기화 (Streamlit에서 데이터 저장 용도)
if 'flocks' not in st.session_state:
    st.session_state.flocks = load_data() # 3. 앱 시작 시 데이터 불러오기


# 계군 추가 콜백
def add_flock_callback(name, hatch_date):
    if not name:
        st.error("계군 이름을 입력해주세요.")
        return
    
    # datetime 객체를 문자열로 저장
    st.session_state.flocks[name] = hatch_date.strftime(DATE_FMT)
    save_data(st.session_state.flocks) # 4. 추가 후 데이터 저장
    st.success(f"✅ 계군 '{name}' (입추일: {hatch_date.strftime(DATE_FMT)})이(가) 등록/업데이트되었습니다.")

# 계군 삭제 콜백
def delete_flock_callback(name_to_delete):
    if name_to_delete in st.session_state.flocks:
        del st.session_state.flocks[name_to_delete]
        save_data(st.session_state.flocks) # 5. 삭제 후 데이터 저장
        st.success(f"🗑️ 계군 '{name_to_delete}'이(가) 삭제되었습니다.")

# --- 메인 앱 설정 ---
st.set_page_config(
    page_title="[회사 이름] 주령 계산기 (다계군)",
    layout="wide",
    initial_sidebar_state="expanded"
)
col1, col2 = st.columns([1, 5]) # 로고와 제목을 위한 컬럼 분할
with col1:
    # 이 부분은 사용자님이 설정한 파일명으로 그대로 두세요.
    st.image("kpts.jpg", width=70) 
with col2:
    st.title("한국양계 다계군 주령 계산기")


today = datetime.now().date()
current_flocks = st.session_state.flocks
sorted_flock_names = sorted(current_flocks.keys())

# ====================
# 사이드바: 계군 관리
# ====================
with st.sidebar:
    st.header("🐑 계군 관리 (입추일 등록)")
    
    # 폼: 계군 등록/수정
    with st.form("flock_add_form"):
        flock_name = st.text_input("계군 이름 (예: A동, 1차)", key="flock_name_input")
        # 기본값은 10주 전으로 설정
        hatch_date = st.date_input("입추일", value=today - timedelta(weeks=10), format="YYYY-MM-DD", key="hatch_date_input")
        
        submitted = st.form_submit_button("➕ 계군 등록/수정", type="primary")

        if submitted:
            add_flock_callback(flock_name.strip(), hatch_date)
            st.rerun() # 등록 후 페이지 새로고침

    st.subheader("등록된 계군 목록")
    if current_flocks:
        # 등록된 계군 정보 표시
        st.dataframe(
            pd.DataFrame([
                (name, current_flocks[name]) 
                for name in sorted_flock_names
            ], columns=['계군 이름', '입추일']),
            hide_index=True,
            use_container_width=True
        )

        # 폼: 계군 삭제
        with st.form("flock_delete_form"):
            flock_to_delete = st.selectbox(
                "삭제할 계군을 선택하세요.",
                [""] + sorted_flock_names,
                index=0,
                key="flock_delete_select",
                label_visibility="collapsed"
            )
            delete_submitted = st.form_submit_button("🗑️ 선택 계군 삭제", disabled=(flock_to_delete == ""))

            if delete_submitted:
                delete_flock_callback(flock_to_delete)
                st.rerun() # 삭제 후 페이지 새로고침

        st.info(f"총 {len(current_flocks)}개 계군이 등록되었습니다.")
    else:
        st.info("현재 등록된 계군이 없습니다. 위에서 계군을 등록해주세요.")


# ====================
# 메인 영역: 계산
# ====================

if not current_flocks:
    st.warning("계산 결과는 왼쪽 사이드바에서 계군을 등록하시면 자동으로 표시됩니다.")
else:
    # 모드 선택
    selected = option_menu(
        menu_title=None,
        options=["1. 일자 → 주령 계산 (현재 주령 확인)", "2. 주령 → 일자 계산 (목표 일자 확인)"],
        icons=["calendar-check", "clock"],
        default_index=0,
        orientation="horizontal",
        styles={
            "nav-link-selected": {"background-color": "#5ab3ff", "color": "white"},
        }
    )
    
    # ============== 모드 1: 일자 -> 주령 계산 ==============
    if selected == "1. 일자 → 주령 계산 (현재 주령 확인)":
        st.subheader("🗓️ 목표 일자 기준 주령 계산")

        with st.form("date_to_week_form"):
            target_date_input = st.date_input("목표 일자", value=today, format="YYYY-MM-DD")
            submitted_calc = st.form_submit_button("✅ 계산 결과 보기", type="primary")

        if submitted_calc or True: # 페이지 로드 시 또는 버튼 클릭 시 계산 실행
            
            target_date = datetime.combine(target_date_input, datetime.min.time())
            
            results_list = []
            for name in sorted_flock_names:
                hatch_date_str = current_flocks[name]
                hatch_date = datetime.strptime(hatch_date_str, DATE_FMT)
                
                total_days, age_text = calculate_age(hatch_date, target_date)
                
                # 결과 테이블 데이터 생성
                results_list.append({
                    "계군 이름": name,
                    "입추일": hatch_date_str,
                    "목표 일자": target_date_input.strftime(DATE_FMT),
                    "일령(일)": total_days,
                    "주령(주+일)": age_text,
                })

            st.markdown("#### 📊 계산 결과 테이블")
            df = pd.DataFrame(results_list)
            st.dataframe(df, hide_index=True, use_container_width=True)


    # ============== 모드 2: 주령 -> 일자 계산 ==============
    elif selected == "2. 주령 → 일자 계산 (목표 일자 확인)":
        st.subheader("📅 목표 주령 기준 일자 계산")

        with st.form("week_to_date_form"):
            col1, col2 = st.columns(2)
            with col1:
                target_weeks = st.number_input("목표 주령 (주)", min_value=0, max_value=100, value=15, key="tw_input")
            with col2:
                target_days = st.number_input("목표 주령 (일)", min_value=0, max_value=6, value=0, key="td_input")

            submitted_calc_2 = st.form_submit_button("✅ 목표 일자 계산 결과 보기", type="primary")

        if submitted_calc_2 or True: # 페이지 로드 시 또는 버튼 클릭 시 계산 실행
            
            results_list = []
            for name in sorted_flock_names:
                hatch_date_str = current_flocks[name]
                hatch_date = datetime.strptime(hatch_date_str, DATE_FMT)
                
                target_date, total_days = calculate_target_date(hatch_date, target_weeks, target_days)
                
                # 결과 테이블 데이터 생성
                results_list.append({
                    "계군 이름": name,
                    "입추일": hatch_date_str,
                    "목표 주령": f"{target_weeks}주 {target_days}일",
                    "일령(일)": total_days,
                    "계산된 일자": format_date_with_weekday(target_date),
                })
            
            st.markdown("#### 📊 계산 결과 테이블")
            df = pd.DataFrame(results_list)
            st.dataframe(df, hide_index=True, use_container_width=True)
