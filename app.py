# app.py 상단 (임포트 확인)

import streamlit as st
import pandas as pd
from datetime import datetime as dt_class, date # ⭐ Changed datetime class to dt_class ⭐
import calendar as pycal
import requests 
from collections import defaultdict 
import io          
import re          
import shutil      
import os          
import openpyxl # ⭐ Added: Necessary for Excel processing. ⭐

from data_manager import DataManager 
from statistics_exporter import StatisticsExporter

# ⭐ 1. Page Configuration: Set title and change layout to 'wide' for full width ⭐
st.set_page_config(
    page_title="Employee Attendance Manager", 
    layout="wide", 
    initial_sidebar_state="expanded" # Start with sidebar expanded if present
)


st.markdown(
    """
    <style>
    /* ... (기존 CSS 스타일 유지) ... */
    
    /* ⭐ 탭 폰트 크기 및 스타일 조정 ⭐ */
    /* 탭 레이블을 포함하는 요소를 타겟팅합니다. */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px; /* 탭 간격 조절 */
    }
    
    .stTabs [data-baseweb="tab"] {
        /* 탭 자체의 패딩 조절 */
        padding: 6px 15px; 
    }
    
    .stTabs [data-baseweb="tab"] > div {
        /* 탭 텍스트를 포함하는 내부 div를 타겟팅합니다. */
        font-size: 20px !important; /* 폰트 크기를 16px로 강제 설정 */
        font-weight: bold;         /* 폰트 굵게 설정 */
        color: #FFFFFF !important;  /* 폰트 색상을 흰색으로 강제 설정 (선택 사항) */
    }
    
    /* ... (기존 CSS 스타일 유지) ... */
    </style>
    """,
    unsafe_allow_html=True
)


# app.py 파일 내의 st.markdown("""<style>...</style>""") 블록을 아래와 같이 수정하세요.

st.markdown(
    """
    <style>
    /* ... 기존 탭 스타일은 생략 ... */
    
    /* 1. SAVE ALL, DELETE ALL 등 모든 st.button의 폰트 크기 강제 조정 */
    /* 버튼 텍스트를 포함하는 내부 요소를 타겟팅합니다. */
    .stButton > button {
        /* 버튼 자체의 높이를 줄여 버튼 크기를 작게 만듭니다. */
        height: 2.5em; /* 2em에서 약간 키워 가독성 확보 */
        line-height: 1.5; 
        padding: 0 10px; /* 내부 패딩을 줄여 버튼을 작게 */
    }

    /* 2. st.button 내부 텍스트에 font-size: 10px을 강제 적용 */
    .stButton > button > div > p, /* Streamlit 1.x ~ 2.x 버전의 일반적인 텍스트 경로 */
    .stButton > button > span {    /* 일부 환경/버전에서의 경로 */
        font-size: 14px !important; /* 10px은 너무 작을 수 있으므로 14px로 권장 */
        font-weight: bold;
        line-height: 1.5;
        white-space: nowrap; /* 텍스트가 줄바꿈되지 않도록 */
    }
    
    /* SAVE ALL, DELETE ALL 버튼의 이모지 크기를 줄이는 것은 CSS로 어렵지만, 
       텍스트 크기를 줄이면 상대적으로 작아 보입니다. */
       
    </style>
    """, 
    unsafe_allow_html=True
)


# ----------------------------------------------------
# 1. CONSTANTS and SETUP
# ----------------------------------------------------

# (Synchronized with data_manager.py)
ALL_STATUS_COLS = ["ATT", "LATE", "WO", "PEL", "ANL", "HAL", "SIL", "SPL", "EVL"]
STATUS_COLORS = {
    "ATT": "#4FC3F7", "LATE": "#F44336", "WO": "#FFFFFF", 
    "PEL": "#FFC107", "ANL": "#00BCD4", "HAL": "#8BC34A", 
    "SIL": "#9C27B0", "SPL": "#FF5722", "EVL": "#607D8B",
    "NONE": "#1E1E1E" 
}
TARGET_CURRENCIES = [
    "USD", "KRW", "IDR", "JPY", "EUR", 
    "CNY", "GBP", "CAD", "AUD", "SGD"
]
CURRENCY_NAMES = {
    "USD": "US Dollar", "KRW": "South Korean Won", "IDR": "Indonesian Rupiah",
    "JPY": "Japanese Yen", "EUR": "Euro", "CNY": "Chinese Yuan",
    "GBP": "British Pound", "CAD": "Canadian Dollar", "AUD": "Australian Dollar",
    "SGD": "Singapore Dollar"
}

# Define all attendance status types
ALL_ATTENDANCE_TYPES = ["hh:mm", "WO", "PEL", "ANL", "HAL", "SIL", "SPL", "EVL"]

# Manual for each TYPE (English)
TYPE_MANUAL = {
    "hh:mm": "Time Input (e.g., 09:00):",
    "WO": "Work Out ",
    "PEL": "Personal Leave",
    "ANL": "Annual Leave ",
    "HAL": "Half-day Leave ",
    "SIL": "Sick Leave ",
    "SPL": "Special Leave ",
    "EVL": "Event Leave"
}

# ----------------------------------------------------
# 2. STATE INITIALIZATION (Session State Management)
# ----------------------------------------------------

# 1. Initialize keys to None to prevent KeyError
if 'dm' not in st.session_state:
    st.session_state['dm'] = None
if 'se' not in st.session_state:
    st.session_state['se'] = None

# 2. Attempt only if DataManager has not been successfully loaded yet
if st.session_state['dm'] is None:
    try:
        # Attempt DataManager initialization
        st.session_state['dm'] = DataManager()
        
        # Initialize StatisticsExporter upon successful DataManager initialization
        st.session_state['se'] = StatisticsExporter(st.session_state['dm'])
        
    except Exception as e:
        # Keep both dm and se as None and display error message on initialization failure
        st.error(f"Data Manager Initialization Error. Check file permissions and paths: {e}")
        st.session_state['dm'] = None
        st.session_state['se'] = None 


# Initialize calendar state
if 'current_year' not in st.session_state:
    st.session_state['current_year'] = date.today().year
if 'current_month' not in st.session_state:
    st.session_state['current_month'] = date.today().month
if 'selected_date' not in st.session_state:
    st.session_state['selected_date'] = date.today().strftime("%Y-%m-%d")

# Assign to global variables (now safe)
dm = st.session_state['dm']
se = st.session_state['se']


# C:\Users\user\Desktop\Cursor\Gemini\Result\_TEI_attendance_web_v5\app.py

# ... (Existing code omitted)

def save_multi_attendance():
    """Batch saves attendance records (time or TYPE) and memo for each employee using DataManager."""
    selected_date = st.session_state.get('selected_date')
    if not selected_date:
        st.error("No date has been selected.")
        return

    employees = dm.get_employee_list()
    data_to_save = {}
    
    # ----------------------------------------------------------------------
    # ⭐ Core Fix: Extract value and determine status from a single input field (emp_input_i) ⭐
    # ----------------------------------------------------------------------
    for i, emp in enumerate(employees):
        input_key = f'emp_input_{i}'
        raw_input = (st.session_state.get(input_key) or "").strip().upper()
        final_record = None
        
        if not raw_input:
            continue 

        # 1. Check HH:MM format (Time Input)
        if re.match(r"^\d{1,2}:\d{2}$", raw_input):
            time_input = raw_input
            
# Retain ATTRIBUTE ERROR fix logic implemented inline in the previous step
            try:
                # 1. Load standard time from settings (standard_time_str variable unified)
                standard_time_str = dm.settings.get('attendance_time', '09:00')
                today_date = date.today().strftime("%Y-%m-%d")
                
                # Parse input time
                # ⭐ Modification: Use dt_class.strptime instead of datetime ⭐
                input_dt = dt_class.strptime(
                    f"{today_date} {time_input}",
                    "%Y-%m-%d %H:%M" 
                )
                
                # Parse standard time
                # ⭐ Modification: Use dt_class.strptime and standard_time_str variable ⭐
                standard_dt = dt_class.strptime(
                    f"{today_date} {standard_time_str}", 
                    "%Y-%m-%d %H:%M"
                )

                if input_dt <= standard_dt:
                    status = "ATT"
                else:
                    status = "LATE"
                    
                # final_record example: "ATT(09:00)" or "LATE(09:15)"
                final_record = f"{status}({time_input})"
            
            # Defensive logic against time format errors and system errors (Optional)
            except ValueError:
                final_record = f"ERROR(Format:{time_input})"
            except Exception:
                final_record = f"ERROR(System)"

                return
            
        # 2. Check TYPE format (WO, ANL, etc.)
        elif raw_input in ALL_ATTENDANCE_TYPES[1:]: # Exclude hh:mm
            # final_record example: "WO" or "ANL"
            final_record = raw_input
            
        # 3. Invalid Input
        else:
            st.error(f"❌ Input value '{raw_input}' for {emp} is not a valid time (HH:MM) or TYPE. Stopping save.")
            return

        if final_record:
            # ⭐ Modification: Store the final status/time to be saved in final_record to data_to_save ⭐
            data_to_save[emp] = final_record
    
    # ----------------------------------------------------
    # 2. Memory Update and Final Save Trigger (Core Modified Section)
    # ----------------------------------------------------
    
    memo_key = f'memo_{selected_date}'
    memo_text = st.session_state.get(memo_key, "").strip() # Remove whitespace
    
    current_day_data = dm.attendance_data.get(selected_date, {})
    old_memo_text = current_day_data.get('__MEMO__', "")

    # Check if record and memo have changed
    memo_changed = (old_memo_text != memo_text)
    record_changed = bool(data_to_save) # If data_to_save has anything, the record changed
    
    if record_changed or memo_changed: # If data to save (attendance/memo) has changed
        
        # 2-1. Initialize data for that date (if necessary)
        if selected_date not in dm.attendance_data:
            dm.attendance_data[selected_date] = {}
            
        # 2-2. Update Memo (Memory)
        if memo_text:
            dm.attendance_data[selected_date]['__MEMO__'] = memo_text
        elif '__MEMO__' in dm.attendance_data[selected_date]:
            del dm.attendance_data[selected_date]['__MEMO__']
            
        # 2-3. Update Attendance Record (Memory) - Directly update instead of dm.save_attendance_record
        for emp, record in data_to_save.items():
            dm.attendance_data[selected_date][emp] = record
            
        # 2-4. Force save Excel file (Run only once after memory update is complete)
        dm.save_internal_data() 
            
        st.success(f"Attendance records ({len(data_to_save)} items) and memo for {selected_date} successfully saved.")
    else:
        st.warning(f"No attendance records or memo content to save.")
        
    # st.rerun() # Keep removed state as before


# ... (Remaining existing code omitted)



def delete_multi_attendance():
    """Deletes all attendance records and memo for the selected date."""
    selected_date = st.session_state.get('selected_date')
    if not selected_date:
        st.error("No date has been selected.")
        return
    
    # Delete all records for the date from DataManager
    dm.delete_all_attendance(selected_date)
    
    # ⭐ Delete Memo (Directly manipulate dm.attendance_data)
    if selected_date in dm.attendance_data and '__MEMO__' in dm.attendance_data[selected_date]:
        del dm.attendance_data[selected_date]['__MEMO__']
    
    st.success(f"🗑️ All attendance records and memo for {selected_date} have been deleted.")
    # ⭐ Remove st.rerun() call. (Fixes no-op warning within callback function)
    # st.rerun()

# ----------------------------------------------------
# 3. HELPER FUNCTIONS
# ----------------------------------------------------

def change_month(offset):
    """Moves the calendar to the previous/next month."""
    st.session_state['current_month'] += offset
    if st.session_state['current_month'] > 12:
        st.session_state['current_month'] = 1
        st.session_state['current_year'] += 1
    elif st.session_state['current_month'] < 1:
        st.session_state['current_month'] = 12
        st.session_state['current_year'] -= 1
    st.session_state['selected_date'] = None
    #st.rerun() 

def select_date(day):
    """Selects the clicked date and loads the input field data.""" 
    if day:
        date_str = f"{st.session_state['current_year']}-{st.session_state['current_month']:02d}-{day:02d}"
        st.session_state['selected_date'] = date_str
        
        # ⭐ Logic to update input field values when a date is selected ⭐
        if dm:
            day_map = dm.attendance_data.get(date_str, {})
            employees = dm.get_employee_list()

            for i, emp in enumerate(employees):
                input_key = f'emp_input_{i}'
                current_record = day_map.get(emp)
                
                # Extract HH:MM from ATT(HH:MM) or LATE(HH:MM)
                if '(' in str(current_record) and ')' in str(current_record):
                    value = current_record.split('(')[-1].strip(')')
                elif isinstance(current_record, str):
                    # TYPE such as WO, ANL, etc.
                    value = current_record.strip()
                else:
                    value = "" # Empty string if no record

                # Set form field value by directly updating Streamlit's Session State
                st.session_state[input_key] = value

            # Update memo input field value
            memo_key = f'memo_{date_str}'
            # ⭐ Modification: Retrieve memo directly using the '__MEMO__' key from dm.attendance_data instead of dm.get_memo. ⭐
            current_memo = dm.attendance_data.get(date_str, {}).get('__MEMO__', "")
            
            st.session_state[memo_key] = current_memo        
    else:
        st.session_state['selected_date'] = None

def get_current_record(emp_name):
    """Gets the employee's record for the selected date."""
    date_str = st.session_state.get('selected_date')
    if not date_str or not dm:
        return None
    
    return dm.attendance_data.get(date_str, {}).get(emp_name)

def save_attendance():
    # This function is superseded by save_multi_attendance, but the existing code is retained.
    if not dm or not st.session_state['selected_date']:
        st.warning("Please select a date or ensure Data Manager (dm) is ready.")
        return

    selected_date = st.session_state['selected_date']
    emp_name = st.session_state['emp_selector']
    status = st.session_state['status_radio']
    time_str = st.session_state['check_in_time']
    
    if emp_name == "Select an Employee":
        st.error("You must select an employee to record for.")
        return
        
    if status in ['ATT', 'LATE'] and (not time_str or len(time_str.split(':')) != 2 or not time_str.replace(':', '').isdigit()):
        st.error("Attendance/Late status requires a valid time input. (e.g., 09:00)")
        return
        
    dm.save_attendance_record(selected_date, emp_name, status, time_str)
    
    st.success(f"Record for {emp_name} on {selected_date} successfully saved.")
    st.rerun() 
    
def fetch_exchange_rates():
    """Calls the exchange rate API and saves the result to the session state."""
    API_URL = "https://open.er-api.com/v6/latest/USD"
    
    st.session_state['exchange_rates'] = None
    st.session_state['exchange_status'] = "Status: Fetching..."
    st.session_state['exchange_time'] = ""

    try:
        response = requests.get(API_URL, timeout=5)
        response.raise_for_status() 
        data = response.json()
        
        if data.get('result') == 'success':
            rates = {
                curr: data['rates'].get(curr) 
                for curr in TARGET_CURRENCIES if data['rates'].get(curr) is not None
            }
            st.session_state['exchange_rates'] = rates
            st.session_state['exchange_status'] = "Status: Last updated at " + data.get('time_last_update_utc', 'N/A')
            st.session_state['exchange_time'] = data.get('time_last_update_utc', '')

        else:
            st.session_state['exchange_status'] = "Status: API Call Failed"
            st.error("Failed to call the exchange rate API.")

    except requests.exceptions.RequestException as e:
        st.session_state['exchange_status'] = f"Status: Network Error"
        st.error(f"Network Error: {e}")
    except Exception as e:
        st.session_state['exchange_status'] = f"Status: Unknown Error"
        st.error(f"An unexpected error occurred: {e}")
        
def generate_pdf_for_download(api_type, year, month):
    """Creates a BytesIO object for the PDF download button."""
    try:
        buffer = io.BytesIO()
        temp_path = "temp_report.pdf"
        
        # Call StatisticsExporter's PDF generation method (temporarily save to file system)
        se.generate_pdf_summary(temp_path, api_type, year, month)
        
        with open(temp_path, "rb") as f:
            buffer.write(f.read())
        
        os.remove(temp_path) 
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"A fatal error occurred while generating the PDF: {e}")
        return None

def generate_excel_for_download(api_type, year, month):
    """Creates a BytesIO object for the Excel download button."""
    try:
        buffer = io.BytesIO()
        temp_path = "temp_report.xlsx"
        
        # Call StatisticsExporter's Excel generation method
        se.export_excel_report(temp_path, api_type, year, month)
        
        with open(temp_path, "rb") as f:
            buffer.write(f.read())
            
        os.remove(temp_path)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"A fatal error occurred while generating the Excel: {e}")
        return None


# ----------------------------------------------------
# 4. UI COMPONENTS (Tabs)
# ----------------------------------------------------

# (Streamlit Main Configuration)
st.set_page_config(
    page_title="Employee Attendance Management Web Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Header ---
# ⭐ Modification 1: Use Markdown H4 tag instead of st.title (Reduced font size) ⭐
# ⭐ Modification 2: Set CSS margin-top: -15px, margin-bottom: 0 to minimize vertical space ⭐
# --- Header ---
st.markdown(
    """
    <h4 style='
    	margin-top: -15px; 
    	margin-bottom: 0; 
    	text-align: center; /* ⭐ Added this line for center alignment ⭐ */
    	font-size: 35px; /* ⭐ Font size modification (e.g., 28px) ⭐ */
    	color: #4FC3F7;   /* ⭐ Added font color (e.g., light blue) ⭐ */
    	font-weight: bold; /* Keep bold */
    '>
    	👨‍💻 Employee Attendance Management System
    </h4>
    """,
    unsafe_allow_html=True
)
# ⭐ Modification 3: Minimize top/bottom margin of the horizontal rule (hr) as well ⭐
st.markdown("<hr style='margin-top: 5px; margin-bottom: 5px;'>", unsafe_allow_html=True)

# Do not draw UI if DataManager is not loaded.
if not dm:
    st.warning("Data Manager load failed: Please register the employee list in the Settings tab and check file permissions to ensure necessary files (settings.json, attendance.json) can be created.")
    st.stop()

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["🗓️ Attendance Record Entry", "📊 Statistics/Reports", "⚙️ Settings", "💵 Exchange Rate Inquiry"])

# ----------------------------------------------------
# TAB 1: Attendance Record (Implementation in AttendanceView_calendar_ctk.py)
# ----------------------------------------------------
with tab1:

    # CSS for vertical expansion of the calendar column (does not affect the entire page)
    st.markdown(
        """
        <style>
        	/* Expand col_calendar area to maximum height */
        	div[data-testid="column"]:nth-child(2) {
        		min-height: 85vh;
        	}
        </style>
        """,
        unsafe_allow_html=True
    )

    # ----------------------------------------------------
    # Divide main layout into 2 columns (Input Form | Calendar)
    # ----------------------------------------------------
    col_input_form, col_calendar = st.columns([2, 8])


# ====================================================
# LEFT COLUMN (col_input_form): Place Attendance Input Form
# ====================================================
with col_input_form:
    st.markdown(
        f"""
        <center>
        <div style="font-size:20px; font-weight:bold; margin-bottom:10px; color: yellow;"> 
            Attendance Records <br> ({st.session_state.get('selected_date', 'Date Not Selected')})
        </div>
        </center>
        """,
        unsafe_allow_html=True
    )
    
    employees = dm.get_employee_list()
    
    # ⭐ Main IF statement starts: The ELSE statement connected to this IF likely caused an error on line 437. ⭐
    if st.session_state.get('selected_date'): 
        
        # Warning if the employee list is empty (First nested IF)
        if not employees:
            st.warning("⚙️ Please first register your employee list in the Settings tab..")
        # Execution if the employee list exists (First nested ELSE)
        else:
            
            # ------------------------------------------------------------------
            # 1. Integrate Single Input Field per Employee
            # ------------------------------------------------------------------
            #st.markdown("##### Enter Attendance Status per Employee")
            
            col_header_emp, col_header_status = st.columns([1, 1], gap="small")
            col_header_emp.markdown("**Employee Name**")
            col_header_status.markdown("**Status/Time**") 

            for i, emp in enumerate(employees):
                col_emp, col_input = st.columns([1, 1], gap="small")
                
                col_emp.markdown(f"**{emp}**")
                
                # NOTE: This get_current_record logic pre-populates st.session_state[key] in the select_date function, 
                # so that value is prioritized.
                current_record = get_current_record(emp)
                if '(' in str(current_record) and ')' in str(current_record):
                    initial_value = current_record.split('(')[-1].strip(')')
                else:
                    initial_value = current_record.strip() if isinstance(current_record, str) else ""

                col_input.text_input(
                    label='_hidden_time_or_type', 
                    key=f'emp_input_{i}',
                    placeholder="HH:MM or TYPE input",
                    label_visibility='collapsed',
                    width='stretch'
                )

            
            # ------------------------------------------------------------------
            # 4. Display Memo Input Field
            # ------------------------------------------------------------------
            st.markdown("##### 📝 Daily Memo")
            memo_key = f'memo_{st.session_state["selected_date"]}'
            current_memo = dm.get_memo(st.session_state["selected_date"]) if hasattr(dm, 'get_memo') else ""
            st.text_area("Memo", value=current_memo, key=memo_key, height=100, label_visibility='collapsed')


            # ------------------------------------------------------------------
            # 5. Add SAVE, DELETE Buttons
            # ------------------------------------------------------------------
            col_save, col_delete = st.columns([1, 1], gap="small")
            
            col_save.button("✅ SAVE ALL", on_click=save_multi_attendance, width='stretch', type="primary")

            col_delete.button("❌ DELETE ALL", on_click=delete_multi_attendance, width='stretch', type="secondary")

            st.markdown("---")
            
            # ------------------------------------------------------------------
            # 3. Display TYPE Manual (English)
            # ------------------------------------------------------------------
            st.markdown("##### 📚 Attendance Type Manual")
            manual_text = ""
            for type_key, description in TYPE_MANUAL.items():
                manual_text += f"**{type_key}**: {description}  \n"
            st.markdown(manual_text)


# ⭐ ELSE statement connected to the Main IF ⭐
# This else: block must have the same indentation level as the if st.session_state.get('selected_date'): immediately above it.
    else:
        st.info("Click a date on the calendar to enter attendance records.")


# ====================================================
# RIGHT COLUMN (col_calendar): Place Calendar and Navigation
# ====================================================
with col_calendar:
    # Calendar Navigation Buttons
    col_nav_prev, col_nav_next = st.columns([1, 1])
    with col_nav_prev:
        # ⭐ Use width='stretch' instead of use_container_width=True ⭐
        st.button("◀️ Previous Month ", on_click=change_month, args=(-1,), key="prev_month_btn_cal", width='stretch')
    with col_nav_next:
        # ⭐ Use width='stretch' instead of use_container_width=True ⭐
        st.button("Next Month ▶️", on_click=change_month, args=(1,), key="next_month_btn_cal", width='stretch')

    # ⭐⭐ Added: Display Current Year/Month at the top center of the calendar (30px font) ⭐⭐
    import datetime # should already be imported at the top.

    # dt_class는 from datetime import datetime as dt_class에서 정의된 별칭입니다.
    current_month_name = dt_class(st.session_state['current_year'], st.session_state['current_month'], 1).strftime("%B %Y")
    
    # 텍스트가 중앙 컬럼의 중앙에 오도록 배치 (기존 스타일 유지)
    st.markdown(
        f"""
        <div style='text-align: center; 
                    font-size: 30px; 
                    font-weight: bold; 
                    margin-bottom: 10px;
                    white-space: nowrap;'>  {current_month_name}
        </div>
        """, 
        unsafe_allow_html=True
    )
    # ⭐⭐ Added End ⭐⭐


    # --- Calendar Grid ---
    cal = pycal.Calendar(pycal.SUNDAY)
    # ... (Rest of the code omitted)    st.markdown("---")

    # --- Calendar Grid ---
    cal = pycal.Calendar(pycal.SUNDAY)
    month_days = cal.monthdatescalendar(
        st.session_state['current_year'],
        st.session_state['current_month']
    )

    # Weekly Header (Sun-Sat)
    header_cols = st.columns(7)
    weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    for i, day in enumerate(weekdays):
        color = "red" if i == 0 or i == 6 else "white"
        header_cols[i].markdown(
            f"<h6 style='text-align: center; color:{color}; font-weight:bold; margin-top:0; margin-bottom:0;'>{day}</h6>",
            unsafe_allow_html=True
        )

    # Create Date Cells
    for week in month_days:
        cols = st.columns(7)
        for i, day_dt in enumerate(week):

            day_str = day_dt.strftime("%Y-%m-%d")

            if day_dt.month != st.session_state['current_month']:
                cols[i].markdown(
                    "<div style='text-align: center; color:grey; font-size: 10px;'>-</div>",
                    unsafe_allow_html=True
                )
                continue

            day_records = dm.attendance_data.get(day_str, {})
            status_summary = defaultdict(int)

            for emp in dm.get_employee_list():
                record = day_records.get(emp)
                status = 'NONE'
                if record:
                    raw_status = record.split('(')[0].strip().upper()
                    status = raw_status if raw_status in STATUS_COLORS else 'WO'
                status_summary[status] += 1

            bg_color = STATUS_COLORS['NONE']
            if status_summary['LATE'] > 0:
                bg_color = STATUS_COLORS['LATE']
            elif status_summary['PEL'] > 0:
                bg_color = STATUS_COLORS['PEL']
            elif status_summary['ANL'] > 0:
                bg_color = STATUS_COLORS['ANL']
            elif status_summary['ATT'] > 0:
                bg_color = STATUS_COLORS['ATT']

            border_style = (
                f"3px solid {STATUS_COLORS['ATT']}"
                if day_str == st.session_state.get('selected_date')
                else "1px solid #444444"
            )

            btn_key = f"day_btn_{day_str}"

            with cols[i]:
                # ⭐ Use width='stretch' instead of use_container_width=True ⭐
                if st.button(
                    str(day_dt.day),
                    key=btn_key,
                    on_click=select_date,
                    args=(day_dt.day,),
                    width='stretch'
                ):
                    pass

               # ... (중략) ...

                record_list = []
                for emp in dm.get_employee_list():
                    record = day_records.get(emp)
                    if record:
                        # 1. Changed 'display_name' to the full 'emp' to display the entire employee name (e.g., Mr. Ray displayed as Mr. Ray)
                        display_name = emp # Original: emp.split(' ')[0]
                        
                        # 2. Display status in uppercase (maintaining existing behavior)
                        # Extract status from attendance record and display in uppercase (e.g., Late(08:40) -> LATE(08:40))
                        # record_list.append(f"{display_name}: {record}") # Original: includes lowercase status
                        
                        # Convert status (LATE, ATT, etc.) in the attendance record to uppercase
                        # Example: 'Late(08:40)' -> 'LATE(08:40)'
                        # Record format: 'Status(Time)'
                        parts = re.split(r'(\(|\))', record, 1) # 'Status', '(', 'Time)'
                        if len(parts) >= 3:
                            status_upper = parts[0].strip().upper()
                            time_info = parts[2] if parts[2].endswith(')') else parts[2] + ')'
                            
                            # ⭐ 수정 시작: 폰트 색상 조건부 지정 ⭐
                            if status_upper == 'ATT':
                                font_color = 'green' # ATT는 Green
                            elif status_upper == 'LATE':
                                font_color = 'red'   # LATE는 Red
                            else:
                                font_color = 'yellow' # WO, PEL, ANL 등 기타는 Yellow

                            # HTML span 태그로 근태 기록 텍스트를 감싸서 색상 적용
                            display_record = f"<span style='color:{font_color};'>{status_upper}{parts[1]}{time_info}</span>"
                            record_list.append(f"{display_name}: {display_record}")
                            # ⭐ 수정 끝 ⭐
                            
                        else:
                            # Use original method for unexpected formats, but status in uppercase (e.g., 'WO')
                            status_upper_simple = record.upper()
                            
                            # ⭐ 수정 시작: Type (WO, PEL 등)에 대한 색상 지정 ⭐
                            if status_upper_simple == 'ATT':
                                font_color = 'green'
                            elif status_upper_simple == 'LATE':
                                font_color = 'red'
                            else:
                                font_color = 'yellow'

                            display_record = f"<span style='color:{font_color};'>{status_upper_simple}</span>"
                            record_list.append(f"{display_name}: {display_record}")
                            # ⭐ 수정 끝 ⭐

                if record_list:
                    # 3. Line break fix: Change join delimiter from '-' to '<br>' for line breaks
                    # Also, the {'-'.join(record_list)} part inside the <p> tag has been changed to '<br>'.join(record_list).
                    ############## Adjust Calendar Cell Info Font Size ###########################
                    
                    # ⭐ 수정 시작: <p> 태그를 <div>로 바꾸고, color: lightgrey 속성을 삭제/수정합니다. ⭐
                    st.markdown(
                        f"""
                        <div style='background-color:{bg_color};
                                     padding: 2px;
                                     border: {border_style};
                                     border-radius: 5px;
                                     margin-top: -30px;
                                     margin-bottom: 5px;
                                     text-align: center;'>
                        </div>
                        <div style='font-size: 16px; margin: 0;'> 
                            {'<br>'.join(record_list)}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    # ⭐ 수정 끝 ⭐

# End of Right Column


# ----------------------------------------------------
# TAB 2: Statistics/Reports (Implemented in attendance_statistics_ctk.py)
# ----------------------------------------------------
with tab2:
    pass    # (Tab 2 content)
    st.header("📊 Attendance Statistics and Reports")
    
    # 1. Select Report Type
    report_type = st.radio(
        "Select Report Type",
        ["Monthly Statistics", "Yearly Statistics", "Overall Statistics"],
        key='report_type_radio',
        horizontal=True
    )
    
    # 2. Enter Period
    current_year = date.today().year
    current_month = date.today().month
    
    year = current_year
    month = current_month
    
    col_type_params, col_empty = st.columns([1, 3])
    
    if report_type == "Monthly Statistics":
        with col_type_params:
            year = st.number_input("Year", min_value=2020, max_value=2050, value=current_year, key='stat_year')
            month = st.number_input("Month", min_value=1, max_value=12, value=current_month, key='stat_month')
            
    elif report_type == "Yearly Statistics":
        with col_type_params:
            year = st.number_input("Year", min_value=2020, max_value=2050, value=current_year, key='stat_year_only')
            month = None
    else:
        year = None
        month = None
        
    # 3. Calculate Statistics Button
    if st.button("Calculate Statistics and View Chart", key="calculate_stats_btn", type="secondary"):
        
        type_map = {"Monthly Statistics": "monthly", "Yearly Statistics": "yearly", "Overall Statistics": "total"}
        api_type = type_map[report_type]
        
        try:
            # Use StatisticsExporter's internal helper function to set period and calculate
            df, title_ko, start_date, end_date = se._get_df_for_period(api_type, year, month)
            
            st.session_state['stats_df'] = df
            st.session_state['stats_title'] = title_ko
            st.session_state['stats_type'] = api_type
            st.session_state['stats_year'] = year
            st.session_state['stats_month'] = month
            
        except Exception as e:
            st.error(f"Statistics Calculation Error: {e}")
            st.session_state['stats_df'] = pd.DataFrame() 
            

    # 4. Display Results
    if 'stats_df' in st.session_state and not st.session_state['stats_df'].empty:
        df_display = st.session_state['stats_df']
        title_ko = st.session_state['stats_title']
        
        st.subheader(f"Result: {title_ko}")
        st.dataframe(df_display, hide_index=True, use_container_width=True)
        
        # 5. Display Chart
        try:
            chart_title = title_ko.replace("근태 통계", "Attendance Statistics") 
            fig = se.create_attendance_chart(df_display.copy(), chart_title)
            st.pyplot(fig)
        except Exception as e:
            st.warning(f"Error occurred during chart creation: {e}. (Can happen if the employee list is empty)")
            
        
        # 6. Export Report Button
        st.subheader("Export Report (Available after calculating statistics)")
        
        col_pdf, col_excel = st.columns(2)
        
        type_for_file = st.session_state['stats_type']
        year_for_file = st.session_state['stats_year']
        month_for_file = st.session_state['stats_month']
        
        # Generate PDF/Excel filename
        filename_base = f"attendance_report_{year_for_file or 'All'}"
        if month_for_file:
            filename_base += f"_{month_for_file:02d}"
        
        # PDF Download
        col_pdf.download_button(
            label="Download PDF Report",
            data=generate_pdf_for_download(type_for_file, year_for_file, month_for_file),
            file_name=f"{filename_base}.pdf",
            mime="application/pdf",
            # ⭐ Use width='stretch' instead of use_container_width=True ⭐
            width='stretch' 
        )
            
        # Excel Download
        col_excel.download_button(
            label="Download Excel Report",
            data=generate_excel_for_download(type_for_file, year_for_file, month_for_file),
            file_name=f"{filename_base}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            # ⭐ Use width='stretch' instead of use_container_width=True ⭐
            width='stretch' 
        )

# ----------------------------------------------------
# TAB 3: Settings (Implemented in settings_view_ctk.py)
# ----------------------------------------------------
with tab3:
    st.header("⚙️ System Settings and Employee Management")
    
    # 1. Employee List Management
    st.subheader("Employee List (One per line)")
    
    current_employees = "\n".join(dm.get_employee_list())
    
    employee_input = st.text_area(
        "Enter the list of employee names and press the 'Save Settings' button:",
        value=current_employees,
        height=200,
        key='employee_list_input'
    )
    
    # 2. Set Attendance Standard Time
    st.subheader("Set Attendance Standard Time")
    
    current_time = dm.settings.get('attendance_time', '09:00')
    time_input = st.text_input(
        "Standard Time (HH:MM)",
        value=current_time,
        #key='attendance_time_input',
        help="E.g., 09:00. If this time is changed, all records will be recalculated."
    )
    
    # 3. Save Settings Button
    if st.button("Save Settings and Recalculate Attendance", key="save_settings_btn", type="primary"):
        new_employees = [e.strip() for e in employee_input.split('\n') if e.strip()]
        new_time = time_input.strip()
        
        # Time format validation
        time_pattern = re.compile(r'^(?:[0-9]|1\d|2[0-3]):[0-5]\d$')

        if not time_pattern.match(new_time):
            st.error("Invalid time format. Please enter in **H:MM or HH:MM format (e.g., 9:00 or 09:00)**.")
            st.stop()
            
        new_settings = {
            'employees': new_employees,
            'attendance_time': new_time
        }
        
        dm.update_settings_and_recalculate(new_settings)
        st.success("Settings successfully saved, and attendance records have been recalculated if the standard time was changed.")
        st.rerun()
        
    st.markdown("---")

    # 4. Data Backup
    st.subheader("Data Backup")
    col_backup, col_info = st.columns(2)
    
    backup_path = "attendance_backups"
    if col_backup.button("Backup Current Data"):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(backup_path, f"backup_{timestamp}")
            os.makedirs(backup_dir, exist_ok=True)
            
            # Copy settings.json and attendance.json files
            shutil.copy("settings.json", backup_dir)
            shutil.copy("attendance.json", backup_dir) 
            
            st.success(f"Data successfully backed up: {backup_dir}")
        except Exception as e:
            st.error(f"Error occurred during backup: {e}")

    col_info.info(f"Data Files: settings.json, attendance.json")

# ----------------------------------------------------
# TAB 4: Exchange Rate Inquiry (Implemented in ExchangeRateViewer.py)
# ----------------------------------------------------
with tab4:
    st.header("💵 Real-time Exchange Rate Information (Based on USD)")
    
    if 'exchange_rates' not in st.session_state:
        fetch_exchange_rates()
    
    col_status, col_button = st.columns([3, 1])
    
    col_status.markdown(st.session_state.get('exchange_status', 'Status: Not Fetched'), unsafe_allow_html=True)
    col_button.button("Refresh", on_click=fetch_exchange_rates, key="refresh_rates")

    rates = st.session_state.get('exchange_rates')
    
    if rates:
        rate_data = {
            "Currency": [f"{CURRENCY_NAMES.get(c, c)} ({c})" for c in TARGET_CURRENCIES],
            "Exchange Rate (Per 1 USD)": [rates.get(c, 0) for c in TARGET_CURRENCIES]
        }
        rate_df = pd.DataFrame(rate_data)
        
        st.dataframe(
            rate_df.style.format({"Exchange Rate (Per 1 USD)": "{:,.2f}"}),
            use_container_width=True,
            hide_index=True
        )