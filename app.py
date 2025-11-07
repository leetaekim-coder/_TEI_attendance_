# app.py

import streamlit as st
from web_data_manager import DataManager
from datetime import date, datetime, timedelta
import pandas as pd
import os
import calendar as pycal 
# ⭐ Matplotlib, NumPy, io import 추가 ⭐
import matplotlib.pyplot as plt
import numpy as np
import io
# ⭐ PIL Image import (그래프 이미지를 메모리에 저장하기 위해 사용) ⭐
from PIL import Image

# 달력 시작 요일 설정: 일요일(0)로 변경
pycal.setfirstweekday(pycal.SUNDAY)

# --- 1. 기본 설정 및 데이터 로드 ---
APP_TITLE = "Employee Attendance Manager (Web Version)" 
st.set_page_config(page_title=APP_TITLE, layout="wide")

# --- 2. 로고 및 메인 타이틀 표시 ---
LOGO_PATH = "./assets/logo.png"

# 로고와 타이틀을 위한 컬럼 분할 (1:8 비율)
# 로고 쪽 비율을 0.8로 줄여서 제목에 더 붙게 시도
logo_col, title_col = st.columns([0.8, 5]) 

with logo_col:
    if os.path.exists(LOGO_PATH):
        # width=150을 유지합니다.
        st.image(LOGO_PATH, width=250)
    else:
        st.empty() 

with title_col:
    # st.markdown을 사용하여 h1 제목을 출력 (CSS 마진 제거 적용)
    st.markdown(f'<h1>{APP_TITLE}</h1>', unsafe_allow_html=True)


st.markdown("""
<style>

/* --- 기존 스타일 그대로 유지하며, 전체화면 구조 절대 변경 없음 --- */

/* 탭 리스트 전체: 브라우저 폭 꽉 채우기 */
div[data-baseweb="tab-list"] {
    display: flex !important;
    justify-content: space-between !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding: 0 !important;
    box-sizing: border-box;
}

/* 각 탭 버튼: 균등 분배 + 반응형 */
button[data-baseweb="tab"] {
    flex: 1 1 0 !important;
    text-align: center !important;
    font-size: 2.2rem !important;     /* 기존보다 2단계 크게 */
    font-weight: 800 !important;
    padding: 22px 0 !important;
    border: none !important;
    border-radius: 0 !important;
    transition: background 0.2s ease;
    background: green !important;     /* 비활성 탭: 녹색 */
    color: black !important;          /* 비활성 탭 폰트: 검정 */
}

/* 선택된 탭 강조 */
button[data-baseweb="tab"][aria-selected="true"] {
    background: blue !important;      /* 활성 탭: 파란색 */
    color: white !important;          /* 활성 탭 폰트: 흰색 */
}

/* 반응형: 폭이 좁아지면 세로 정렬 */
@media (max-width: 768px) {
    div[data-baseweb="tab-list"] {
        flex-direction: column !important;
    }
    button[data-baseweb="tab"] {
        width: 100% !important;
    }
}

/* --- 출석 입력란 직원 이름 폰트 확대 (2단계) --- */
.stTextInput label p,
.stTextInput label,
.stTextInput label span,
.stTextInput label div {
    font-size: 1.7rem !important;     
    font-weight: 700 !important;
    color: #003399 !important;        /* 진한 파랑 */
}

/* 입력 필드 내부 텍스트 크기 */
.stTextInput input,
.stTextArea textarea,
.stSelectbox div[data-baseweb="select"] input {
    font-size: 1.3rem !important;
}

/* --- Settings Management 하단 입력란 직원명 폰트 확대 (2단계) --- */
section[data-testid="stSidebar"] label,
div[data-testid="stVerticalBlock"] label,
div[data-testid="stVerticalBlock"] p {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
}

section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea,
section[data-testid="stSidebar"] select {
    font-size: 1.6rem !important;
}

/* --- 통계탭 내 그래프 크기 축소 (1/2 사이즈로) --- */
.element-container:has(canvas),
.element-container:has(svg) {
    transform: scale(0.7) !important;     /* 그래프 전체 1/2로 축소 */
    transform-origin: top center !important;
}

/* --- 1️⃣ 달력 셀 내부 텍스트 (작게 유지) --- */
div[data-testid="stMarkdownContainer"].calendar-cell p {
    font-size: 1.1rem !important;
    line-height: 1.1rem !important;
    color: #333 !important;
}

/* --- 2️⃣ Selected Date / Daily Memo 텍스트만 확대 --- */
div[data-testid="stMarkdownContainer"]:not(.calendar-cell) h3,
div[data-testid="stMarkdownContainer"]:not(.calendar-cell) h2,
div[data-testid="stMarkdownContainer"]:not(.calendar-cell) p strong {
    font-size: 1.5rem !important;
    font-weight: 800 !important;
    color: white !important;
    line-height: 1.3 !important;
}

/* ====== Selected Date / Daily Memo 전용 스타일 (명확하고 안전) ====== */

/* Selected Date 텍스트 (더 크게, 굵게) */
.selected-date {
    font-size: 1.2rem !important;       /* 원하시면 값 조정 가능 */
    font-weight: 800 !important;
    color: white !important;
    margin-bottom: 0.5rem !important;
}

/* 내부의 strong 부분(날짜 값)을 약간 더 강조 */
.selected-date strong {
    font-size: 1.2rem !important;
    font-weight: 900 !important;
    color: white !important;

}

/* Daily Memo 제목 */
.daily-memo {
    font-size: 1.2rem !important;
    font-weight: 800 !important;
    color: white !important;
    margin-top: 1rem !important;
    margin-bottom: 0.4rem !important;
}

</style>
""", unsafe_allow_html=True)






if 'data_manager' not in st.session_state:
    try:
        st.session_state.data_manager = DataManager()
    except Exception as e:
        st.error(f"Data Manager Initialization Failed: {e}") 
        st.stop()

dm = st.session_state.data_manager
ATTENDANCE_FILE = dm.ATTENDANCE_FILE 
MEMO_COLUMN = dm.MEMO_COLUMN

# ⭐ 세션 상태 초기화 ⭐
today = date.today()
if 'current_year' not in st.session_state:
    st.session_state.current_year = today.year # Calendar Year/Monthly Stats Year
if 'current_month' not in st.session_state:
    st.session_state.current_month = today.month # Calendar Month/Monthly Stats Month
if 'selected_date_str' not in st.session_state:
    st.session_state.selected_date_str = today.strftime("%Y-%m-%d")

# ⭐ New: Independent state for Yearly Stats Navigation (Fix 2) ⭐
if 'stats_year' not in st.session_state:
    st.session_state.stats_year = today.year

# 월 이동 함수
def _prev_month():
    current_date = date(st.session_state.current_year, st.session_state.current_month, 1)
    new_date = current_date.replace(day=1) - timedelta(days=1)
    st.session_state.current_year = new_date.year
    st.session_state.current_month = new_date.month

def _next_month():
    current_date = date(st.session_state.current_year, st.session_state.current_month, 1)
    if st.session_state.current_month == 12:
        st.session_state.current_year += 1
        st.session_state.current_month = 1
    else:
        st.session_state.current_month += 1

def _go_today():
    today = date.today()
    st.session_state.current_year = today.year
    st.session_state.current_month = today.month
    st.session_state.selected_date_str = today.strftime("%Y-%m-%d")

# ... (나머지 도우미 함수: parse_raw_attendance_input, get_input_default_value, get_status_color, _on_day_click) ...
def parse_raw_attendance_input(raw_input: str, standard_time: str) -> str:
    """
    Converts raw_input (HH:MM or PV/CV/WO) to the final status string (ATT(HH:MM), LATE(HH:MM), PV, CV, WO).
    """ 
    text = raw_input.strip().upper()
    if text in ["PV", "CV", "WO"]: return text

    try:
        if ':' not in text and text.isdigit():
            if len(text) == 3: text = '0' + text
            if len(text) == 4: text = text[:2] + ':' + text[2:]
            else: raise ValueError("Not a recognizable time format")

        time_obj = datetime.strptime(text, '%H:%M').time()
        input_time = time_obj.strftime('%H:%M')

        standard_dt = datetime.strptime(standard_time, '%H:%M')
        input_dt = datetime.strptime(input_time, '%H:%M')

        if input_dt <= standard_dt:
            return f"ATT({input_time})"
        else:
            return f"LATE({input_time})"

    except (ValueError, IndexError, TypeError):
        return f"ATT({standard_time})"

def get_input_default_value(full_status: str, standard_time: str) -> str:
    """Extracts the default value to display in the input field from the existing status string.""" 
    if not isinstance(full_status, str): return standard_time
    
    status_only = full_status.split('(')[0] if '(' in full_status else full_status
    time_only = full_status.split('(')[1].strip(')') if '(' in full_status and ')' in full_status else standard_time
    
    if status_only.upper() in ["PV", "CV", "WO"]:
        return status_only
    else:
        return time_only

def get_status_color(status):
    """Returns text color based on attendance status.""" 
    if status.startswith('ATT'): return '#90EE90' # LightGreen
    if status.startswith('LATE'): return '#FFA07A' # LightSalmon
    if status in ['WO', 'PV', 'CV']: return '#FFD700' # Gold
    return '#FFFFFF' # White

def _on_day_click(day, year, month):
    selected_date = date(year, month, day)
    st.session_state.selected_date_str = selected_date.strftime("%Y-%m-%d")


# --- 4. Calendar Rendering Function (render_calendar은 변경 없음) ---
def render_calendar(dm):
    
    year = st.session_state.current_year
    month = st.session_state.current_month
    today_str = date.today().strftime("%Y-%m-%d")
    
    HOLIDAY_BG_COLOR = "#6B1F1F" 

    # 1. Navigation Header
    col_prev, col_title, col_next, col_today = st.columns([1, 4, 1, 1])
    col_prev.button("◀ Previous Month", on_click=_prev_month, use_container_width=True)
    
    col_title.markdown(f"<h3 style='text-align: center; color: #4FC3F7;'>{date(year, month, 1).strftime('%B %Y')}</h3>", unsafe_allow_html=True) 
    
    col_next.button("Next Month ▶", on_click=_next_month, use_container_width=True)
    col_today.button("Today", on_click=_go_today, type="primary", use_container_width=True)

    # 2. Weekday Header
    week_cols = st.columns(7)
    day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] 
    for i, day_name in enumerate(day_names):
        color = 'red' if i in [0, 6] else 'white'
        week_cols[i].markdown(
            f"<p style='text-align: center; color: {color}; font-weight: bold;'>{day_name}</p>",
            unsafe_allow_html=True
        )

    # 3. Calendar Data Generation
    cal_iterator = pycal.Calendar(pycal.SUNDAY)
    month_days_with_weekday = list(cal_iterator.itermonthdays2(year, month))
    
    # 4. Calendar Rendering
    
    for r in range(0, len(month_days_with_weekday), 7):
        week = month_days_with_weekday[r:r+7]
        if not week: break

        day_cols = st.columns(7)
        for i, (day, weekday) in enumerate(week):
            
            day_cols[i].empty()
            
            is_current_month = (day != 0)
            target_date = None

            if day == 0:
                if r == 0: 
                    first_day_weekday = week[0][1]
                    target_date = date(year, month, 1) - timedelta(days=first_day_weekday - i)
                else: 
                    days_in_current_month = pycal.monthrange(year, month)[1]
                    days_into_next_month = i - (7 - (len(month_days_with_weekday) - r))
                    target_date = date(year, month, days_in_current_month) + timedelta(days=days_into_next_month + 1)
                    
                date_str = target_date.strftime("%Y-%m-%d")
                day_display = str(target_date.day)
                
            else:
                current_date = date(year, month, day)
                date_str = current_date.strftime("%Y-%m-%d")
                day_display = str(day)
                target_date = current_date

            
            is_selected = date_str == st.session_state.selected_date_str
            is_today = date_str == today_str
            
            holiday_name = dm.get_holiday_name(date_str)
            is_holiday = holiday_name is not None
            
            if is_selected:
                bg_color = "#2E7D32" 
            elif is_holiday: 
                bg_color = HOLIDAY_BG_COLOR
            elif is_today:
                bg_color = "#01579B"
            elif not is_current_month: 
                bg_color = "#121212" 
            else:
                bg_color = "#1E1E1E"


            day_records = dm.attendance_data.get(date_str, {})
            attendance_info_list = []
            
            for emp in dm.settings.get('employees', []):
                v = day_records.get(emp)
                if v and v != dm.MEMO_COLUMN:
                    status_name = v.split('(')[0]
                    color = get_status_color(status_name)
                    
                    display_text = f"<span style='color:white;'>{emp}</span>"
                    if '(' in v:
                        time_part = v.split('(')[1].strip(')')
                        display_text += f": <span style='color:{color};'>{time_part}</span>" 
                    else:
                        display_text += f": <span style='color:{color};'>{status_name}</span>" 
                    
                    attendance_info_list.append(
                        f"<p style='margin:0; line-height:1.2; font-size:18px;'>{display_text}</p>"
                    )
            
            holiday_html = ""
            if holiday_name:
                holiday_html = f"<p style='color:#FFCCCC; font-size:16px; font-weight:bold; margin:0;'>{holiday_name}</p>"

            if attendance_info_list:
                records_html = holiday_html + "".join(attendance_info_list)
            elif holiday_name:
                records_html = holiday_html
            else:
                records_html = "<p style='color:grey; font-size:18px; margin:0;'>No Record</p>"

            today_tag = f'<div style="color:#4FC3F7; font-size:12px;">(Today)</div>' if is_today else ''
            
            day_color = "white" if is_current_month else "#AAAAAA" 

            with day_cols[i]:
                st.markdown(
                    f'<div id="day_cell_{date_str}" style="background-color:{bg_color}; border-radius:10px; padding:2px; text-align:left; overflow:hidden;">'
                    f'<div style="color:{day_color}; font-weight:bold; font-size:16px;">{day_display}</div>'
                    f'{today_tag}'
                    f'<div>{records_html}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                
                st.button(
                    " ", 
                    key=f"btn_day_{date_str}",
                    on_click=_on_day_click,
                    args=(target_date.day, target_date.year, target_date.month),
                    use_container_width=True
                )
# --- render_calendar function end ---


# --- 5. UI Configuration (Tabs) ---
# st.title(APP_TITLE)  <-- ⭐ 이 줄을 삭제합니다. ⭐
st.markdown(f"Standard Check-in Time: **{dm.attendance_standard_time}** | Number of Employees: **{len(dm.employees)}**")

tab1, tab2, tab3 = st.tabs(["📅 Attendance", "📊 Statistics", "⚙ Settings"]) 

# --------------------------------------------------------------------------------------------------
# Tab 1: Attendance (로직 변경 없음)
# --------------------------------------------------------------------------------------------------
with tab1:
    st.header("Attendance Record and Input")

    col_input, col_calendar = st.columns([1.0, 3.0])

    with col_calendar:
        render_calendar(dm)

    selected_date_str = st.session_state.selected_date_str

    with col_input:

        # Selected Date — 클래스를 붙여서 명확히 타겟팅
        st.markdown(
            f"<div class='selected-date'>Selected Date: <strong>{selected_date_str}</strong></div>",
            unsafe_allow_html=True
        )

        records = dm.get_day_records(selected_date_str)

        with st.form(key='attendance_form', clear_on_submit=False):

            st.markdown("##### Employee Status Input (HH:MM, H:MM or PV, CV, WO)")
            employee_raw_inputs = {}

            cols = st.columns(1)
            col = cols[0]

            for i, emp in enumerate(dm.employees):

                full_status = records.get(emp, f"ATT({dm.attendance_standard_time})")
                input_default = get_input_default_value(full_status, dm.attendance_standard_time)

                with col:
                    input_text = st.text_input(
                        label=f"**{emp}**",
                        value=input_default,
                        key=f"{emp}_input_{selected_date_str}"
                    )

                    employee_raw_inputs[emp] = input_text

            st.markdown("---")
            st.markdown("<div class='daily-memo'>Daily Memo</div>", unsafe_allow_html=True)
            default_memo = records.get(MEMO_COLUMN, "")
            memo = st.text_area(
                "Enter Memo",
                default_memo,
                key=f'memo_{selected_date_str}'
            )

            col_save, col_delete = st.columns(2)

            submitted = col_save.form_submit_button("✅ Save Record", type="primary", use_container_width=True)
            deleted = col_delete.form_submit_button("🗑️ Delete Record", use_container_width=True)

            if submitted:
                final_records = {}
                for emp, raw_input in employee_raw_inputs.items():
                    final_records[emp] = parse_raw_attendance_input(raw_input, dm.attendance_standard_time)

                dm.save_attendance_record(selected_date_str, final_records, memo)
                st.success(f"Record for **{selected_date_str}** saved successfully.")

            if deleted:
                if st.session_state.get(f'confirm_delete_{selected_date_str}', False):
                    if selected_date_str in dm.attendance_data:
                        del dm.attendance_data[selected_date_str]
                        dm._save_attendance_data()
                        st.success(f"Record for **{selected_date_str}** deleted successfully.")
                        st.session_state[f'confirm_delete_{selected_date_str}'] = False
                    else:
                        st.warning("No record to delete.")
                        st.session_state[f'confirm_delete_{selected_date_str}'] = False

                else:
                    st.session_state[f'confirm_delete_{selected_date_str}'] = True
                    st.warning("⚠️ **Are you sure you want to delete?** Press 'Delete Record' again.")



# --------------------------------------------------------------------------------------------------
# Tab 2: Statistics (수정 완료)
# --------------------------------------------------------------------------------------------------

# --- 그래프 렌더링 함수 (Fix 1, Fix 3 포함) ---
def render_stats_section(df: pd.DataFrame, title_suffix: str):
    """그룹화된 막대 그래프를 렌더링하고 Excel 다운로드 버튼을 표시합니다."""
    
    st.subheader(f"Attendance Status Visualization: {title_suffix}")  
    
    if df.empty or 'Employee' not in df.columns or len(df.index) == 0:
        st.info(f"No records available for {title_suffix}.")
        # 엑셀 다운로드 버튼도 표시하지 않음
        st.markdown("---")
        return

    # 'Employee' 열을 인덱스로 설정하고 'Total' 열은 드롭
    try:
        chart_data = df.set_index('Employee').drop(columns=['Total'], errors='ignore')
    except KeyError:
        chart_data = df.set_index('Employee')

    # 1. 데이터 준비 및 설정 (이전과 동일)
    categories = chart_data.columns.tolist() 
    employees = chart_data.index.tolist()
    data = chart_data.values 

    x = np.arange(len(employees))  
    width = 0.15 

    colors = {
        'ATT': '#34A853', # Green
        'LATE': '#FBBC05', # Yellow
        'WO': '#EA4335', # Red
        'CV': '#4285F4', # Blue
        'PV': '#A142F4'  # Purple
    }
    
    # 2. Figure 생성 및 배경색 설정 (크기 절반, 배경 옅은 블랙)
    fig, ax = plt.subplots(
        figsize=(5, 2.5), 
        # ⭐ 1차 수정: constrained_layout=True 추가 (레이아웃 잘림 방지) ⭐
        constrained_layout=True 
    ) 
    
    fig.patch.set_facecolor('#333333') 
    ax.set_facecolor('#333333')        
    
    text_color = 'white'
    ax.tick_params(axis='x', colors=text_color, labelsize=8) 
    ax.tick_params(axis='y', colors=text_color, labelsize=8) 
    ax.yaxis.label.set_color(text_color)        
    ax.title.set_color(text_color)              
    
    # 3. 막대 그리기
    for i, category in enumerate(categories):
        offset = x - (len(categories) / 2 - i) * width 
        ax.bar(offset, data[:, i], width, label=category, color=colors.get(category))

    # 4. 축 레이블 및 제목 설정
    ax.set_xticks(x)
    ax.set_xticklabels(employees, rotation=0, ha='center', fontsize=8) 
    ax.set_ylabel('Count', fontsize=8) 
    ax.set_title(f"{title_suffix} Attendance Status", fontsize=10) 
    
    # 막대 그래프 상단에 숫자 카운터 표시
    for container in ax.containers:
        ax.bar_label(container, label_type='edge', color='white', fontsize=8)

    # ⭐ 2차 수정: Y축 범위 조정 (숫자 카운터 잘림 방지) ⭐
    # y축의 범위 조정 
    if not df.empty and not df.drop('Employee', axis=1).empty:
        max_val = df.drop('Employee', axis=1).values.max()
        # 1.15를 1.30으로 수정하여 충분한 여백 확보
        ax.set_ylim(top=max_val * 1.30) 
    
    # ⭐ 범례 위치 Fix (Fix 1: 우측에 세로로) ⭐
    # bbox_to_anchor와 loc='center left'를 사용하여 Axes 외부에 배치
    legend = ax.legend(
        bbox_to_anchor=(1.05, 0.5), # Axes의 오른쪽 중앙 (1.05)에 배치
        loc='center left',            # 범례의 왼쪽 중앙을 앵커에 맞춤
        ncol=1,                       # 세로 한 줄로 나열
        facecolor='#333333',
        edgecolor='white',
        fontsize=7, 
        title='Status'
    )
    plt.setp(legend.get_texts(), color=text_color) 
    plt.setp(legend.get_title(), color=text_color)
    
    plt.tight_layout()

    # 5. Streamlit에 Matplotlib 그래프 표시
    st.pyplot(fig)
    
    # ---------------------------------------------
    # ⭐ Excel Export (Fix 2: 그래프 이미지 포함) ⭐
    # ---------------------------------------------
    
    # 그래프를 PNG 이미지로 메모리에 저장
    img_buffer = io.BytesIO()
    fig.savefig(img_buffer, format='png', bbox_inches='tight', facecolor='#333333')
    img_buffer.seek(0)
    
    plt.close(fig) # 메모리 누수 방지

    # Pandas ExcelWriter를 사용하여 DataFrame을 쓰고 이미지를 삽입
    excel_buffer = io.BytesIO()
    
    # writer 객체 생성 (openpyxl 엔진 사용)
    writer = pd.ExcelWriter(excel_buffer, engine='openpyxl')
    
    # 1. 통계 데이터 DataFrame 쓰기
    df.to_excel(writer, index=False, sheet_name='Statistics Data')
    
    # 2. 이미지 삽입 로직
    try:
        workbook = writer.book
        worksheet = writer.sheets['Statistics Data']

        # PIL Image 객체 생성
        img = Image.open(img_buffer)
        
        # Openpyxl 이미지 객체 생성 및 크기 조절 (원본 크기)
        from openpyxl.drawing.image import Image as OpenpyxlImage
        openpyxl_img = OpenpyxlImage(img)

        # 이미지 삽입 위치 지정 (예: 데이터 테이블 아래 B2 셀에서 시작한다고 가정, A열은 비워둠)
        # 데이터가 끝난 후 한 칸 띄어서 삽입
        image_insert_row = len(df) + 3
        
        # 이미지 삽입 (C3 셀부터 시작)
        worksheet.add_image(openpyxl_img, f'C{image_insert_row}') 
        
    except ImportError:
        # openpyxl이 없으면 이미지를 삽입하지 못하고 경고를 표시합니다.
        st.warning("Cannot embed graph image: 'openpyxl' is required. Data will be saved without the graph.")
    except Exception as e:
        st.error(f"Error embedding image in Excel: {e}")
        
    # writer 저장
    writer.close()
    excel_buffer.seek(0)
        
    st.download_button(
        label=f"Download {title_suffix} Data & Graph (Excel)", 
        data=excel_buffer,
        file_name=f'attendance_{title_suffix.replace(" ", "_").replace("(", "").replace(")", "")}_stats.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        type='primary'
    )



with tab2:
    st.title("📊 Attendance Statistics")

    if not dm.employees or not dm.attendance_data:
        st.warning("No employees or attendance records found to generate statistics.")
    
    else: 
        
        # ---------------------------------------------
        # 1. Monthly Data (월별 통계)
        # ---------------------------------------------
        current_month_date = date(st.session_state.current_year, st.session_state.current_month, 1)
        st.header(f"📅 Monthly Data: {current_month_date.strftime('%Y년 %m월')}")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.button("⬅️ Previous Month", on_click=_prev_month, key="stat_prev_month")
        with col3:
            st.button("Next Month ➡️", on_click=_next_month, key="stat_next_month")

        month_start = current_month_date
        next_month = month_start.replace(day=28) + timedelta(days=4)
        month_end = next_month.replace(day=1) - timedelta(days=1)
        
        monthly_stats_df = dm.calculate_stats(month_start, month_end)
        render_stats_section(monthly_stats_df, "Monthly Data")

        # ---------------------------------------------
        # 2. Yearly Data (연간 통계 - Fix 2 적용: stats_year 사용)
        # ---------------------------------------------
        st.header(f"🗓️ Yearly Data: {st.session_state.stats_year}년")

        col_y1, col_y2, col_y3 = st.columns([1, 2, 1])
        with col_y1:
            # ⭐ Fix 2: stats_year만 업데이트 ⭐
            st.button("⬅️ Previous Year", on_click=lambda: st.session_state.__setitem__('stats_year', st.session_state.stats_year - 1), use_container_width=True, key="prev_year_btn")
        with col_y3:
            # ⭐ Fix 2: stats_year만 업데이트 ⭐
            st.button("Next Year ➡️", on_click=lambda: st.session_state.__setitem__('stats_year', st.session_state.stats_year + 1), use_container_width=True, key="next_year_btn")

        # ⭐ Fix 2: stats_year를 사용하여 계산 ⭐
        year_start = date(st.session_state.stats_year, 1, 1)
        year_end = date(st.session_state.stats_year, 12, 31)
        
        yearly_stats_df = dm.calculate_stats(year_start, year_end)
        render_stats_section(yearly_stats_df, "Yearly Data")

        # ---------------------------------------------
        # 3. Overall Data (전체 통계)
        # ---------------------------------------------
        st.header("🌐 Overall Data (Total)")
        overall_stats_df = dm.calculate_stats()
        render_stats_section(overall_stats_df, "Overall Data (Total)")

# --------------------------------------------------------------------------------------------------
# Tab 3: Settings (로직 변경 없음)
# --------------------------------------------------------------------------------------------------
with tab3:
    st.header("Settings Management") 
    
    with st.form(key='settings_form'):
        
        st.markdown("**Standard Check-in Time**") 
        new_attendance_time_str = st.text_input(
            "Check-in Time (HH:MM format, e.g., 08:30)", 
            dm.attendance_standard_time
        )
        
        st.markdown("**Employee List (one per line)**") 
        employees_str = "\n".join(dm.employees)
        new_employees_str = st.text_area(
            "Employee Names", 
            employees_str,
            height=300 # 원하는 픽셀 값으로 조정하세요 (예: 150, 200, 250 등)
        )
        
        settings_submitted = st.form_submit_button("Save and Apply Settings", type="primary") 
        
        if settings_submitted:
            new_employees = [e.strip() for e in new_employees_str.split('\n') if e.strip()]
            
            try:
                datetime.strptime(new_attendance_time_str, '%H:%M')
            except ValueError:
                st.error("Invalid time format. Please use HH:MM.") 
                st.stop()

            # ⭐ 1. 변경 전 출근 기준 시간 저장 ⭐
            old_attendance_time = dm.attendance_standard_time
                
            # 2. 새로운 설정 저장 (dm 내부의 설정 및 standard time 갱신)
            dm.save_new_settings(new_attendance_time_str, new_employees)
            
            # ⭐ 3. 출근 기준 시간이 변경된 경우, 전체 기록 재계산 및 RERUN ⭐
            if new_attendance_time_str != old_attendance_time:
                # 3-1. 기존 데이터 재계산 (저장된 ATT/LATE 상태 문자열을 업데이트)
                dm.recalculate_all_attendance(new_attendance_time_str)
                st.success(f"Settings saved successfully. All **{len(dm.attendance_data)}** attendance records re-evaluated based on new standard time **{new_attendance_time_str}**.") 
                # 3-2. Streamlit 강제 재실행 (UI/캘린더의 재로드 시 재계산된 데이터 반영)
                st.rerun() 
            else:
                st.success("Settings saved successfully.") 
            
    st.markdown("---")
    st.subheader("Download Existing Data Files") 
    
    if os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, "rb") as file:
            st.download_button(
                label=f"Download '{ATTENDANCE_FILE}'", 
                data=file,
                file_name=ATTENDANCE_FILE,
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
    SETTINGS_FILE = 'settings.json'
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "rb") as file:
            st.download_button(
                label=f"Download '{SETTINGS_FILE}'", 
                data=file,
                file_name=SETTINGS_FILE,
                mime='application/json'
            )