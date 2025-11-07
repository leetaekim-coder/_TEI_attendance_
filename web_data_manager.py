# web_data_manager.py
import json
import os
from datetime import datetime
import pandas as pd
from collections import defaultdict

import streamlit as st # Streamlit secrets 접근을 위해 추가

# Google Sheets 라이브러리 추가
import gspread
from gspread_dataframe import set_with_dataframe, get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials

SETTINGS_FILE = 'settings.json'


class DataManager:
    """웹 버전(Streamlit)을 위한 데이터 관리 클래스"""

    ATTENDANCE_FILE = 'attendance.xlsx'
    MEMO_COLUMN = 'MEMO'

# ⭐ Secrets에서 Sheets 정보 로드 ⭐
    # secrets.toml에 설정한 키(key) 이름을 사용합니다.
    SPREADSHEET_URL = st.secrets["sheet_url"]
    GSHEETS_CREDENTIALS = st.secrets["gcp_service_account"]

    def __init__(self):

        # ⭐ GSheets 클라이언트 초기화 ⭐
        self._gsheet_client = self._get_gsheet_client()
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

# ⭐ Sheets 클라이언트 연결 메서드 수정 ⭐
    def _get_gsheet_client(self):
        # 1. secrets에서 받은 JSON 문자열을 파이썬 딕셔너리로 변환
        #    (이 과정이 없으면 'str' object has no attribute 'get' 오류 발생)
        key_dict = json.loads(self.GSHEETS_CREDENTIALS)
        
        # 2. 딕셔너리 객체를 credential 객체로 변환
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            key_dict, # ⭐ 수정된 부분: 문자열 대신 딕셔너리 객체 사용 ⭐
            ['https://www.googleapis.com/auth/spreadsheets']
        )
        return gspread.authorize(creds)

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

    def _load_attendance_data(self):
        """Google Sheets에서 출석 데이터를 로드합니다."""
        try:
            # 시트 열기
            spreadsheet = self._gsheet_client.open_by_url(self.SPREADSHEET_URL)
            worksheet = spreadsheet.worksheet("Sheet1") # 시트 이름이 'Sheet1'이라고 가정

            # DataFrame으로 데이터 읽기 (Pandas 호환)
            # header=0: 1행(A1)부터 헤더로 사용 (기본값)
            df = get_as_dataframe(worksheet, header=0, skiprows=0) 

            # 유효성 검사 및 인덱스 설정
            if '날짜' not in df.columns:
                 st.error("Google Sheets에 '날짜' 컬럼이 없습니다. 컬럼 헤더를 확인해주세요.")
                 return {}

            df.set_index('날짜', inplace=True)
            # 값이 모두 비어있는 행 제거
            df.dropna(how='all', inplace=True)
            
            # DataFrame을 기존의 attendance_data 딕셔너리 구조로 변환
            # T.to_dict()는 {날짜(인덱스): {컬럼(직원/메모): 값}} 형식으로 변환합니다.
            attendance_map = df.T.to_dict()

            data = {}
            for date_key, emp_map in attendance_map.items():
                # 날짜를 문자열 YYYY-MM-DD 형식으로 통일
                if isinstance(date_key, pd.Timestamp):
                    date_str = date_key.strftime('%Y-%m-%d')
                else:
                    date_str = str(date_key).strip()
                
                cleaned_map = {}
                for k, v in emp_map.items():
                    # NaN 값 (빈 셀) 처리 및 문자열 안전 처리
                    if pd.notna(v) and str(v).strip() != "":
                        # HTML 태그나 공백 제거 및 안전 처리 (기존 로직 유지)
                        safe_val = str(v).replace("<", "&lt;").replace(">", "&gt;")
                        cleaned_map[k] = safe_val

                data[date_str] = cleaned_map

            st.info(f"Google Sheets에서 **{len(data)}**일의 출석 데이터를 로드했습니다.")
            return data

        except gspread.exceptions.SpreadsheetNotFound:
            st.error("Google Sheets 파일을 찾을 수 없습니다. URL과 공유 권한을 확인해주세요.")
            return {}
        except Exception as e:
            st.error(f"Google Sheets 로드 오류 발생: {e}")
            return {}


    def _save_attendance_data(self):
        """Google Sheets에 현재 출석 데이터를 저장합니다."""
        try:
            # 1. 딕셔너리 데이터를 Sheets에 적합한 DataFrame으로 변환
            rows = []
            for date_str, emp_map in self.attendance_data.items():
                row = {'날짜': date_str}
                row.update(emp_map) 
                rows.append(row)
            
            # DataFrame 생성 시, 컬럼 순서를 '날짜' + 직원 + 'MEMO' 순으로 정확히 유지해야 합니다.
            # 이 순서는 Google Sheets의 헤더 순서와 일치해야 합니다.
            columns = ['날짜'] + self.settings.get("employees", []) + [self.MEMO_COLUMN]
            df = pd.DataFrame(rows).reindex(columns=columns)
            
            # NaN (빈 셀)을 빈 문자열로 채워 Sheets에 깔끔하게 저장
            df = df.fillna("")

            # 2. Sheets에 저장
            spreadsheet = self._gsheet_client.open_by_url(self.SPREADSHEET_URL)
            worksheet = spreadsheet.worksheet("Sheet1")
            
            # 기존 데이터를 덮어쓰기 (A1 셀부터 DataFrame 내용으로 채웁니다)
            set_with_dataframe(
                worksheet, 
                df, 
                row=1, 
                col=1, 
                include_index=False, 
                include_column_header=True
            ) 
            # st.info("데이터가 Google Sheets에 성공적으로 저장되었습니다.") # (Streamlit 앱이 성공 시 메시지 표시)

        except Exception as e:
            st.error(f"Google Sheets 저장 오류 발생: {e}")
            print(f"[ERROR] Failed to save data to GSheets: {e}") # 터미널 로그 출력


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
