# web_data_manager.py
import json
import os
from datetime import datetime
import pandas as pd
from collections import defaultdict

SETTINGS_FILE = 'settings.json'


class DataManager:
    """웹 버전(Streamlit)을 위한 데이터 관리 클래스"""

    ATTENDANCE_FILE = 'attendance.xlsx'
    MEMO_COLUMN = 'MEMO'

    def __init__(self):
        self.settings = self._load_settings()
        self.attendance_data = self._load_attendance_data()
        self.employees = self.settings.get("employees", [])

        # 1. settings.json에서 출근 기준 시간 로드
        standard_time_from_settings = self.settings.get("attendance_time", "08:30")
        self.attendance_standard_time = standard_time_from_settings 
        
        # 2. ⭐ 핵심 수정: 앱 시작 시 로드된 모든 기록을 최신 기준으로 재평가 ⭐
        # 이 로직이 누락되어 9:00 설정 후 재시작해도 08:30 기준의 색상이 보였습니다.
        if hasattr(self, 'recalculate_all_attendance'):
            self.recalculate_all_attendance(standard_time_from_settings)

# web_data_manager.py 파일 내 DataManager 클래스에 추가

    def _re_evaluate_time_status(self, old_status_str: str, new_standard_time: str) -> str:
        """
        'ATT(HH:MM)' 또는 'LATE(HH:MM)' 문자열을 새 기준 시간에 맞춰 재계산합니다.
        PV/CV/WO 등은 그대로 반환합니다.
        """
        # PV, CV, WO 등 시간 기반 기록이 아닌 경우 바로 반환
        if not old_status_str or old_status_str in ["PV", "CV", "WO"]:
            return old_status_str
        
        # 1. 시간 부분 추출: "ATT(HH:MM)" -> "HH:MM"
        time_part = old_status_str.split('(')[1].strip(')') if '(' in old_status_str else None
        
        if not time_part: 
            return old_status_str 

        try:
            standard_dt = datetime.strptime(new_standard_time, '%H:%M')
            input_dt = datetime.strptime(time_part, '%H:%M')
            
            # 2. 새로운 기준에 따른 상태 판별
            if input_dt <= standard_dt:
                return f"ATT({time_part})"
            else:
                return f"LATE({time_part})"
                
        except ValueError:
            return old_status_str # 시간 포맷 오류 시 원본 반환

    def recalculate_all_attendance(self, new_standard_time: str):
        """
        출근 기준 시간이 변경되었을 때, 기존의 모든 ATT/LATE 기록을 새 기준에 맞게 재계산합니다.
        """
        recalculated = False
        
        for date_str, day_records in self.attendance_data.items():
            for emp in self.employees:
                old_status = day_records.get(emp)
                
                # 시간 기반 기록만 재계산 대상 (PV, CV, WO는 제외)
                if old_status and (old_status.startswith('ATT(') or old_status.startswith('LATE(')):
                    new_status = self._re_evaluate_time_status(old_status, new_standard_time)
                    
                    if new_status != old_status:
                        day_records[emp] = new_status
                        recalculated = True
                        
        if recalculated:
            self._save_attendance_data()
        
        # 재계산 후 DataManager 내부의 표준 시간 업데이트
        self.attendance_standard_time = new_standard_time



    # -------------------------------
    # 설정 로드 / 저장
# -------------------------------
    def _load_settings(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 'holidays' 키가 누락되지 않도록 기본값에 포함
                return {"attendance_time": "8:30", "employees": [], "holidays": {}} 
        except Exception:
            return {"attendance_time": "8:30", "employees": [], "holidays": {}}

    def _save_settings(self):
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Failed to save settings: {e}")

# ⭐ 새로 추가된 메서드 ⭐
    def get_holiday_name(self, date_str: str) -> str | None:
        """
        주어진 날짜 문자열(YYYY-MM-DD)에 해당하는 휴일 이름(기념일)을 반환합니다.
        """
        return self.settings.get('holidays', {}).get(date_str)

    # -------------------------------
    # 출석 데이터 로드 / 저장
    # -------------------------------
    def _load_attendance_data(self):
        """출석 데이터를 attendance.xlsx에서 로드"""
        if not os.path.exists(self.ATTENDANCE_FILE):
            print(f"[WARN] Attendance file not found: {self.ATTENDANCE_FILE}")
            return {}

        try:
            # Excel → DataFrame
            df = pd.read_excel(self.ATTENDANCE_FILE, dtype=str)
        except Exception as e:
            print(f"[ERROR] Failed to read Excel file: {e}")
            return {}

        # 날짜 컬럼 이름이 '날짜'로 되어 있다고 가정
        if '날짜' not in df.columns:
            print("[ERROR] Excel file missing '날짜' column.")
            return {}

        df = df.set_index('날짜')

        # NaN -> 빈 문자열로 변환
        df = df.fillna("")

        # 각 날짜별 사전으로 변환
        attendance_map = df.to_dict('index')

        data = {}
        for date_key, emp_map in attendance_map.items():
            # 날짜를 문자열 YYYY-MM-DD 형식으로 통일
            if isinstance(date_key, datetime):
                date_str = date_key.strftime('%Y-%m-%d')
            else:
                date_str = str(date_key).strip()

            # 모든 값은 문자열화 + HTML 안전 처리
            cleaned_map = {}
            for k, v in emp_map.items():
                if pd.notna(v) and str(v).strip() != "":
                    # HTML 태그나 공백 제거
                    safe_val = str(v).replace("<", "&lt;").replace(">", "&gt;")
                    cleaned_map[k] = safe_val

            data[date_str] = cleaned_map

        print(f"[INFO] Loaded {len(data)} days of attendance data.")
        return data

    def _save_attendance_data(self):
        """출석 데이터를 attendance.xlsx로 저장"""
        try:
            df = pd.DataFrame.from_dict(self.attendance_data, orient='index')
            df.index.name = '날짜'
            df = df.fillna("")
            df.to_excel(self.ATTENDANCE_FILE, sheet_name='Sheet1', engine='openpyxl')
        except Exception as e:
            print(f"[ERROR] Failed to save attendance data: {e}")

    # -------------------------------
    # 인터페이스 메서드
    # -------------------------------
    def get_day_records(self, date_str):
        """특정 날짜의 출석 기록 반환"""
        # Excel에서 불러온 데이터는 모두 문자열 사전 형태
        record = self.attendance_data.get(date_str, {})
        if self.MEMO_COLUMN not in record:
            record[self.MEMO_COLUMN] = ""
        return record

    def save_attendance_record(self, date_str, records, memo):
        """특정 날짜의 출석 기록 저장"""
        day_map = {k: (str(v) if v is not None else "") for k, v in records.items()}
        day_map[self.MEMO_COLUMN] = memo
        self.attendance_data[date_str] = day_map
        self._save_attendance_data()

    def save_new_settings(self, new_time, new_employees):
        """설정(출근 시간, 직원 목록) 저장"""
        self.settings['attendance_time'] = new_time
        self.settings['employees'] = new_employees
        self.employees = new_employees
        self.attendance_standard_time = new_time
        self._save_settings()

# ... (DataManager 클래스 내부)

    def calculate_stats(self, start_date=None, end_date=None):
        """
        직원별 통계 계산.
        :param start_date: 검색 시작 날짜 (datetime.date 객체 또는 None)
        :param end_date: 검색 종료 날짜 (datetime.date 객체 또는 None)
        """
        employees = self.employees
        status_cols = ["ATT", "LATE", "WO", "CV", "PV"]
        
        # DataFrame 초기화 (Employee를 인덱스로 설정)
        rows = [{"Employee": emp, "ATT": 0, "LATE": 0, "WO": 0, "CV": 0, "PV": 0} for emp in employees]
        df = pd.DataFrame(rows).set_index('Employee') 

        for date_str, emp_map in self.attendance_data.items():
            try:
                # 1. 날짜 문자열을 datetime.date 객체로 변환
                current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                continue # 잘못된 날짜 형식 스킵

            # 2. 기간 필터링 로직
            if start_date and current_date < start_date:
                continue
            if end_date and current_date > end_date:
                continue

            # 3. 통계 카운트 로직 (기존과 동일)
            for emp in employees:
                v = emp_map.get(emp)
                if not v:
                    continue

                raw = str(v).upper()
                status = None
                
                if raw.startswith('ATT('):
                    status = 'ATT'
                elif raw.startswith('LATE('):
                    status = 'LATE'
                elif raw == 'WO': # 명시적 체크
                    status = 'WO'
                elif raw == 'CV': # 명시적 체크
                    status = 'CV'
                elif raw == 'PV': # 명시적 체크
                    status = 'PV'
                # WO, CV, PV가 괄호 없이 문자열만 있는 경우를 명시적으로 처리

                if status and status in df.columns:
                    df.loc[emp, status] += 1
        
        # 'Total' 합계 계산
        df['Total'] = df.sum(axis=1)
        
        # 'Employee' 인덱스를 다시 컬럼으로 복원
        return df.reset_index()