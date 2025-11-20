# data_manager.py (수정 및 보강)

import json
import os
import re
from datetime import datetime, date, timedelta
from collections import defaultdict
import pandas as pd
import shutil
import calendar as pycal # 캘린더 계산을 위해 추가

# ----------------------------------------------------
# DataManager Class
# ----------------------------------------------------

class DataManager:
    # --- [핵심 수정: 경로 오류 해결] File Paths ---
    SETTINGS_FILE_PATH = "settings.json"  # 설정 파일 (JSON 유지)
    ATTENDANCE_FILE_PATH = "attendance.xlsx"  # 출석 기록 파일 (Excel로 변경)
    EXCEL_OUTPUT_PATH = "attendance_summary.xlsx"
    BACKUP_FOLDER = 'attendance_backups'
    
    # Constants
    ALL_STATUS_COLS = ["ATT", "LATE", "WO", "PEL", "ANL", "HAL", "SIL", "SPL", "EVL"]


    def __init__(self):
        """DataManager를 초기화하고 파일 경로를 설정합니다."""
        
        # 1. 설정 로드 (settings.json)
        self.settings = self._load_settings()
        
        # 2. 출석 데이터 로드 (attendance.xlsx)
        self.attendance_data = self._load_attendance_data() 

        # 3. 기준 시간 재계산
        current_time = self.settings.get('attendance_time')
        if current_time:
            self.recalculate_all_attendance(current_time)

    # ----------------------------------------------------
    # --- 헬퍼: 파일 I/O (JSON - Settings용) ---
    # ----------------------------------------------------
    
    def _load_json(self, file_path, default_data=None):
        """JSON 데이터를 파일에서 로드합니다. 파일이 없거나 오류 발생 시 기본값을 반환합니다."""
        if not file_path:
            # 빈 경로 오류 방지
            raise FileNotFoundError("File path is empty. (WinError 3 fix)")
            
        try:
            if not os.path.exists(file_path):
                 return default_data if default_data is not None else {}
                 
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
            print(f"[ERROR] Failed to load {file_path}. Error: {e}. Initializing with default data.")
            return default_data if default_data is not None else {}

    def _save_json(self, data, file_path):
        """JSON 데이터를 파일에 저장합니다."""
        if not file_path:
            print("[ERROR] Cannot save: File path is empty.")
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Failed to save {file_path}. Error: {e}")

    def _load_settings(self):
        """설정 데이터를 로드합니다. (settings.json 사용)"""
        default_settings = {
            'employees': [], 
            'attendance_time': '09:00',
            'appearance_mode': 'dark',
            'color_theme': 'blue',
            'font_size': 12
        }
        return self._load_json(DataManager.SETTINGS_FILE_PATH, default_settings)

    # ----------------------------------------------------
    # --- [핵심 수정] 헬퍼: 파일 I/O (Excel - Attendance Data용) ---
    # ----------------------------------------------------

    def _load_attendance_data(self):
        """
        출석 데이터를 attendance.xlsx 파일에서 로드하고, 내부 포맷(Dict[str, Dict[str, str]])으로 변환합니다.
        """
        file_path = DataManager.ATTENDANCE_FILE_PATH
        if not os.path.exists(file_path):
            print(f"[INFO] Attendance Excel file not found: {file_path}. Starting with empty data.")
            return {}
            
        try:
            # 1. Excel 파일 로드 (Date를 index로 사용)
            df = pd.read_excel(file_path, index_col=0, engine='openpyxl')
            
            # Index 이름을 'Date'로 표준화
            df.index.name = 'Date'
            
            # 2. DataFrame을 내부 데이터 구조(Dict[str, Dict[str, str]])로 변환
            final_data = {}
            for index, row in df.iterrows():
                # 인덱스(날짜) 문자열 포맷팅 (기존 로직 유지)
                if isinstance(index, datetime) or isinstance(index, date):
                    date_str = index.strftime("%Y-%m-%d")
                elif isinstance(index, str):
                    date_str = index
                else:
                    continue 

                daily_records = {}
                
                # ⭐ 수정: 유효한 기록과 MEMO를 구분하여 추출 ⭐
                for col, record in row.items():
                    if pd.notna(record) and str(record).strip():
                        record_str = str(record).strip()
                        
                        # MEMO 컬럼은 특수 키로 저장
                        if col == 'MEMO':
                            daily_records['__MEMO__'] = record_str
                        # 나머지 컬럼(직원명)은 근태 기록으로 저장 (기존 로직 유지)
                        else:
                            daily_records[col] = record_str
                
                if daily_records:
                    final_data[date_str] = daily_records
                    
            return final_data

        except Exception as e:
            print(f"[ERROR] Failed to load attendance data from Excel. Error: {e}")
            return {}



    def _save_attendance_data(self):
        """
        내부 출석 데이터를 DataFrame으로 변환하여 attendance.xlsx 파일에 저장합니다.
        """
        file_path = DataManager.ATTENDANCE_FILE_PATH
        
        # 1. 내부 딕셔너리를 DataFrame으로 변환
        if not self.attendance_data:
            # ⭐ 수정: 빈 DataFrame 생성 시 'MEMO' 컬럼 포함
            columns = self.get_employee_list() + ['MEMO']
            df = pd.DataFrame(columns=columns)
        else:
            # orient='index'로 변환하여 날짜가 Index로 오도록 함
            df = pd.DataFrame.from_dict(self.attendance_data, orient='index')
        
        # ⭐ 핵심 수정 1: '__MEMO__' 컬럼 이름을 'MEMO'로 변경
        if '__MEMO__' in df.columns:
            df = df.rename(columns={'__MEMO__': 'MEMO'})
            
        # ⭐ 핵심 수정 2: 직원 컬럼과 MEMO 컬럼 순서를 재정렬
        employee_cols = self.get_employee_list()
        final_cols = []
        
        # 1. 직원 컬럼 추가 (settings에 정의된 순서 유지)
        for emp in employee_cols:
            if emp in df.columns:
                final_cols.append(emp)
                
        # 2. MEMO 컬럼을 가장 마지막에 추가 (존재하는 경우)
        if 'MEMO' in df.columns:
            final_cols.append('MEMO')
        
        # 3. 누락될 수 있는 다른 컬럼(예: 기존에 존재했지만 settings에 없는 직원)을 추가
        existing_cols = set(df.columns)
        for col in existing_cols:
            if col not in final_cols:
                final_cols.append(col)
            
        # DataFrame을 재정렬된 컬럼 순서로 만듦
        df = df.reindex(columns=final_cols)
        
        # Index 이름을 'Date'로 설정
        df.index.name = 'Date'
        
        # 2. Excel 파일 저장
        try:
            # openpyxl 엔진을 명시하여 저장
            df.to_excel(file_path, engine='openpyxl')
        except Exception as e:
            print(f"[ERROR] Failed to save attendance data to Excel. Error: {e}")

# data_manager.py (기존 함수들 사이에 추가)

    # ----------------------------------------------------
    # --- 유틸리티 및 삭제 로직 (app.py에서 사용됨) ---
    # ----------------------------------------------------
    
    def delete_all_attendance(self, date_str):
        """특정 날짜의 모든 근태 기록과 메모를 삭제하고 Excel 파일을 업데이트합니다."""
        if date_str in self.attendance_data:
            # 해당 날짜의 항목을 딕셔너리에서 제거 (직원 기록 및 __MEMO__ 포함)
            del self.attendance_data[date_str]
            # Excel 파일 업데이트
            self._save_attendance_data()
            return True
        return False
        
    def save_internal_data(self):
        """
        내부 메모리(self.attendance_data)를 기반으로 Excel 파일을 강제 저장합니다. 
        (app.py에서 근태 기록 없이 메모만 변경 시 호출용)
        """
        self._save_attendance_data()



    # ----------------------------------------------------
    # --- 메인 비즈니스 로직 ---
    # ----------------------------------------------------

    def get_employee_list(self):
        """현재 직원 목록을 반환합니다."""
        return self.settings.get('employees', [])

    def save_attendance_record(self, date_str, employee_name, status, time_str=None):
        """단일 근태 기록을 저장하고 Excel 파일을 업데이트합니다."""
        
        if date_str not in self.attendance_data:
            self.attendance_data[date_str] = {}
            
        record = self.attendance_data[date_str]
        
        if status == 'NONE':
            if employee_name in record:
                del record[employee_name]
            if not record:
                del self.attendance_data[date_str]
        else:
            # ATT, LATE 상태에만 시간을 기록
            time_info = f"({time_str})" if time_str and status in ['ATT', 'LATE'] else ""
            record[employee_name] = f"{status}{time_info}"
            
        self._save_attendance_data() # Excel 저장

    def update_settings_and_recalculate(self, new_settings):
        """설정을 업데이트하고, 필요한 경우 모든 근태 기록을 재계산합니다."""
        
        old_time = self.settings.get('attendance_time')
        new_time = new_settings.get('attendance_time')
        
        # 1. 설정 저장 (JSON)
        self.settings.update(new_settings)
        self._save_json(self.settings, DataManager.SETTINGS_FILE_PATH)
        
        # 2. 기준 시간이 변경되었거나 직원 목록이 변경된 경우
        old_employees = set(self.get_employee_list())
        new_employees = set(new_settings.get('employees', []))
        
        # 직원 목록이 변경된 경우, Excel 파일을 새로 저장하여 컬럼을 동기화합니다.
        if old_employees != new_employees:
             self._save_attendance_data() 
            
        if old_time != new_time:
            self.recalculate_all_attendance(new_time) 

    def recalculate_all_attendance(self, new_attendance_time):
        """
        기준 출근 시간을 기반으로 모든 '출석' 및 '지각' 기록을 재계산하고 Excel을 저장합니다.
        """
        recalculated_count = 0
        
        # ⭐ 수정: 기준 출근 시간 파싱 시 유효성 검사 및 예외 처리 추가 ⭐
        try:
            h, m = map(int, new_attendance_time.split(':'))
            standard_time_delta = timedelta(hours=h, minutes=m)
        except ValueError as e:
            # 유효하지 않은 포맷인 경우 경고 출력 및 함수 종료
            print(f"[ERROR] Invalid standard attendance time format: '{new_attendance_time}'. Expected HH:MM.")
            # 이 오류가 발생했다는 것은 UI에서 유효성 검사가 누락되었음을 의미합니다.
            return # 재계산 없이 함수를 종료합니다.
        
        # (기존 코드 유지)
        for date_str, records in self.attendance_data.items():
            for emp_name, record_str in records.items():
                match = re.match(r'(ATT|LATE)\((.+)\)', record_str, re.IGNORECASE)
                
                if match:
                    time_str = match.group(2)
                    try:
                        # 이 부분은 이미 try-except로 처리되어 있어 유지합니다.
                        check_h, check_m = map(int, time_str.split(':'))
                        check_time_delta = timedelta(hours=check_h, minutes=check_m)
                        
                        new_status = 'ATT' if check_time_delta <= standard_time_delta else 'LATE'
                        new_record_str = f"{new_status}({time_str})"
                        
                        if new_record_str != record_str:
                            self.attendance_data[date_str][emp_name] = new_record_str
                            recalculated_count += 1
                    except ValueError:
                        pass
        
        if recalculated_count > 0:
            self._save_attendance_data()

    # --- 통계 계산 헬퍼 (기존 로직 유지) ---
    
    def _get_start_end_dates(self, period_type, year=None, month=None):
        """주어진 기간 유형에 해당하는 시작일과 종료일을 반환합니다."""
        if period_type == 'total':
            return None, None
            
        elif period_type == 'yearly':
            if not year: year = date.today().year
            start = datetime(year, 1, 1).date()
            end = datetime(year, 12, 31).date()
            return start, end
            
        elif period_type == 'monthly':
            if not year: year = date.today().year
            if not month: month = date.today().month
            
            last_day = pycal.monthrange(year, month)[1]
            start = datetime(year, month, 1).date()
            end = datetime(year, month, last_day).date()
            return start, end
            
        return None, None

# data_manager.py

# ... (다른 메서드들)

    # ⭐ 수정 1: 인자(매개변수)를 통계 뷰의 호출 방식에 맞게 변경합니다. ⭐
    def calculate_attendance_stats(self, start_date=None, end_date=None, is_total=False):
        """지정된 기간에 대한 직원별 근태 통계를 DataFrame으로 반환합니다.
        
        Args:
            start_date (str/None): 시작 날짜 ('YYYY-MM-DD' 형식 또는 None).
            end_date (str/None): 종료 날짜 ('YYYY-MM-DD' 형식 또는 None).
            is_total (bool): 전체 기간(전체 데이터)에 대한 통계인지 여부.
        """
        employees = self.get_employee_list()
        if not employees:
            return pd.DataFrame()
            
        df = pd.DataFrame({'Employee': employees})
        
        for col in self.ALL_STATUS_COLS:
            df[col] = 0
            
        # ⭐ 수정 2: start_date, end_date 인자를 datetime.date 객체로 변환합니다. ⭐
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
        
        # is_total이 True이면 전체 기간을 대상으로 합니다.
        if is_total:
            # 전체 기간을 대상으로 할 경우, 시작/종료 날짜 객체를 None으로 설정합니다.
            start_date_obj = None
            end_date_obj = None

        for date_str, emp_map in self.attendance_data.items():
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                continue

            # ⭐ 수정 3: 날짜 객체를 사용하여 기간 필터링을 수행합니다. ⭐
            # start_date_obj가 있고 d가 시작일보다 작으면 건너뜁니다.
            if start_date_obj and d < start_date_obj: continue
            # end_date_obj가 있고 d가 종료일보다 크면 건너뜁니다.
            if end_date_obj and d > end_date_obj: continue
                
            for emp in employees:
                v = emp_map.get(emp)
                status = None
                
                if isinstance(v, str):
                    raw = v.split('(')[0].strip().upper()
                    if raw in df.columns:
                        # 통계 업데이트 로직 (기존 로직 유지)
                        df.loc[df['Employee'] == emp, raw] += 1
                        
        return df

# ⭐ 참고: 이제 _get_start_end_dates 메서드는 사용되지 않으므로, 삭제하거나 주석 처리할 수 있습니다. ⭐