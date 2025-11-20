import customtkinter as ctk
import tkinter as tk
from datetime import date, datetime
import calendar as pycal
from tkinter import messagebox 

class AttendanceCalendarCTK(ctk.CTkFrame):
        
    STATUS_COLORS = {
        "ATT": "#4FC3F7",   # Blue (파랑 - 기준 시간 이전)
        "LATE": "#F44336",  # Red (빨강 - 지각)
        "WO": "#FFFFFF",    # White (흰색)
        # 기존 PV, CV 삭제
        
        # ⭐ 새로운 상태 추가 ⭐
        "PEL": "#FFC107",   # Amber (개인 긴급 휴가)
        "ANL": "#00BCD4",   # Cyan (연차)
        "HAL": "#8BC34A",   # Light Green (반차)
        "SIL": "#9C27B0",   # Purple (병가)
        "SPL": "#FF5722",   # Deep Orange (특별 휴가)
        "EVL": "#607D8B",   # Blue Gray (교육)
        
        "NONE": "#2E2E2E",  # 기본 배경색
        "TEXT": "#FFFFFF"   # 기본 텍스트 색상 (날짜 등)
    }

    #CELL_BG = "#2E2E2E" # 통일된 셀 배경색
    CELL_BG = "#1A1A1A" # 통일된 셀 배경색

    # ⭐ 핵심 수정: 누락된 주말 색상 상수를 추가합니다. ⭐
    SUNDAY_COLOR = "#3F3F3F"    # 일요일 색상
    SATURDAY_COLOR = "#333344"  # 토요일 색상 (약간 푸른 빛이 도는 어두운 색)

    HIGHLIGHT_BG = "#444444" # 클릭 시 배경색 (더 밝은 어두운 회색)
    HOLIDAY_BG = "#FF0000" # ⭐ 추가됨: 공휴일 배경색 정의 ⭐
    #TODAY_BG = "#1A1A1A" # ⭐ 추가됨: 오늘 날짜 셀을 위한 딥 블랙 ⭐
    TODAY_BG = "#6A1B9A" # ⭐ 추가됨: 오늘 날짜 셀을 위한 딥 블랙 ⭐

    
    # ------------------ 초기화 및 기본 설정 ------------------
    def __init__(self, master, data_manager):

        pycal.setfirstweekday(pycal.SUNDAY)   # ← 달력 생성 전 가장 먼저 설정

        # ⭐ RuntimeError 해결 핵심 수정: 폰트 정의를 __init__ 내부로 이동 ⭐
        self.DATE_FONT = ctk.CTkFont(family="Malgun Gothic", size=12, weight="bold")
        self.CALENDAR_FONT = ctk.CTkFont(family="Malgun Gothic", size=10)

        self.HOLIDAY_FONT = ctk.CTkFont(family="Malgun Gothic", size=8, weight="bold")
        self.HEADER_FONT = ctk.CTkFont(family="Malgun Gothic", size=12, weight="bold")
        self.SUB_HEADER_FONT = ctk.CTkFont(family="Malgun Gothic", size=10, weight="bold")

        super().__init__(master, corner_radius=10)
        self.data_manager = data_manager
        today = date.today()
        self.year = today.year
        self.month = today.month
        
        self.employees = data_manager.settings.get("employees", [])
        self.attendance_standard_time = data_manager.settings.get("attendance_time", "08:30")
        
        self.attendance_records = {} 
        self.selected_date_str = today.strftime("%Y-%m-%d")
        self.current_highlighted_card = None 

        # -----------------------------------------------------------------------
        # --- 2. 달력 격자 레이아웃 설정 (세로 확장 문제 해결의 핵심) ---
        # -----------------------------------------------------------------------
        
        # 0행: 년/월 컨트롤 패널 (고정 - 높이 변화 없음)
        self.grid_rowconfigure(0, weight=0)
        
        # 1행: 요일 헤더 (고정 - 높이 변화 없음)
        self.grid_rowconfigure(1, weight=0)
        
        # 2행 ~ 7행: 날짜 셀 (6주 분, 세로 균등하게 확장)
        for i in range(2, 8):
            # ⭐ 수정: 모든 날짜 행이 균등하게 확장되도록 weight=1 설정 ⭐
            self.grid_rowconfigure(i, weight=1) 
            
        # 0열 ~ 6열: 요일 열 (가로 균등하게 확장)
        for i in range(7):
            # ⭐ 수정: 모든 요일 열이 균등하게 확장되도록 weight=1 설정 ⭐
            self.grid_columnconfigure(i, weight=1) 

        # 8행: 메모/근태 입력 폼 (고정 - 높이 변화 없음)
        self.grid_rowconfigure(8, weight=0)

        # __init__ 안에 추가
        self.TITLE_FONT = ctk.CTkFont(family="Malgun Gothic", size=16, weight="bold")    

        self._build_ui()
        self.refresh_records() 
        self._draw_calendar()
        # ⭐ FIX: 위젯 생성(_build_input_form)을 데이터 업데이트(_update_input_form)보다 먼저 호출해야 합니다. ⭐
        self._build_input_form() 
        self._update_input_form()



    # AttendanceView_calendar_ctk.py 파일 내 AttendanceCalendarCTK 클래스 내부

    def refresh_calendar(self):
        """달력 뷰를 갱신합니다. (gui_manager_calendar_ctk.py에서 호출됨)"""
        # _draw_calendar 함수는 달력 UI를 실제로 그리는 함수로 가정합니다.
        self._draw_calendar()
        self._update_input_form() # 입력 폼도 갱신하는 함수가 있다면 함께 호출

    def refresh_records(self):
        try:
            self.attendance_records = self.data_manager.get_all_attendance_records() or {}
        except Exception:
            self.attendance_records = getattr(self.data_manager, "attendance_data", {})

    # ------------------ UI 구성 ------------------
    def _build_ui(self):
        # 1. 2-컬럼 레이아웃 설정 (입력 폼과 달력 프레임 배치)
        # column 0: 입력 폼 (고정 너비)
        self.grid_columnconfigure(0, weight=0) 
        # column 1: 달력 (확장)
        self.grid_columnconfigure(1, weight=1) 
        self.grid_rowconfigure(0, weight=1)

        # 2. 출석 입력 폼 프레임 (왼쪽, column=0)
        self.input_form_frame = ctk.CTkFrame(self, corner_radius=0)
        self.input_form_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew") 
        self.input_form_frame.grid_rowconfigure(99, weight=1) # 하단에 빈 공간 확보

        # 3. 달력 프레임 (오른쪽, column=1)
        self.calendar_frame = ctk.CTkFrame(self, corner_radius=0)
        self.calendar_frame.grid(row=0, column=1, padx=0, pady=0, sticky="nsew") 
        
        # 4. ⭐ [핵심 수정] 달력 프레임 내부 레이아웃 설정 ⭐
        # 달력 프레임 내부는 1x1 구조로, calendar_frame_container가 모든 공간을 차지해야 합니다.
        self.calendar_frame.grid_columnconfigure(0, weight=1) 
        self.calendar_frame.grid_rowconfigure(0, weight=1) # 이 줄이 누락되어 달력 내용이 보이지 않았을 수 있습니다.

        # 5. 달력 콘텐츠를 담을 내부 컨테이너 (스크롤 기능이 없는 일반 프레임 가정)
        # 이 프레임을 calendar_frame 내부의 (0, 0) 위치에 배치하고 확장하도록 합니다.
        self.calendar_frame_container = ctk.CTkFrame(self.calendar_frame, corner_radius=0)
        # ⭐ [핵심 수정] pack 대신 grid를 사용하여 부모 (self.calendar_frame) 내부를 완전히 채우도록 합니다.
        self.calendar_frame_container.grid(row=0, column=0, sticky="nsew") 
        
        # Build Calendar UI elements 
        # 달력 상단의 네비게이션 헤더 (월/년, 버튼 포함)
        header = ctk.CTkFrame(self.calendar_frame_container, corner_radius=8)
        # 사이즈 최소화를 위해 pady (2, 1) 적용
        header.pack(fill="x", padx=8, pady=(2, 1))

        self.prev_btn = ctk.CTkButton(header, text="◀", width=40, height=25, command=self._prev_month)
        self.prev_btn.pack(side="left", padx=4, pady=2) 
        
        self.today_btn = ctk.CTkButton(header, text="Today", width=60, height=25, command=self._go_to_today)
        self.today_btn.pack(side="left", padx=4, pady=2) 
        
        # 월/년도 라벨
        # ⭐ 수정 1: 폰트 크기를 기존 16에서 1/2 크기인 8로 줄이고, 중앙 배치는 pack(expand=True)로 유지합니다. ⭐
        self.title_label = ctk.CTkLabel(
            header, 
            text="", 
            font=ctk.CTkFont(size=8, weight="bold"), # 1/2 사이즈 폰트 적용
            text_color="#FFFFFF" # 텍스트 색상 명시
        )
        self.title_label.pack(side="top", expand=True)
        
        self.next_btn = ctk.CTkButton(header, text="▶", width=40, height=25, command=self._next_month)
        self.next_btn.pack(side="right", padx=4, pady=2) 
        
        # Weekday labels (Sun ~ Sat)
        weekdays = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]
        # ⭐ 수정 2: 요일 프레임 배경색을 구분하기 쉽게 설정 (선택 사항, 기존 기능 유지) ⭐
        days_frame = ctk.CTkFrame(self.calendar_frame_container, corner_radius=0, fg_color="#3A3A3A") 
        days_frame.pack(fill="x", padx=8, pady=0) 
        
        for i in range(7):
            days_frame.grid_columnconfigure(i, weight=1)
            
        for i, d in enumerate(weekdays):
            # ⭐ 수정 3: 일요일(i=0)과 토요일(i=6)에 색상을 적용하여 달력 본체와 통일합니다. ⭐
            text_color = self.SUNDAY_COLOR if i == 0 else (self.SATURDAY_COLOR if i == 6 else self.STATUS_COLORS["TEXT"])
            
            lbl = ctk.CTkLabel(
                days_frame, 
                text=d, 
                width=1, 
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=text_color # 색상 적용
            ) 
            # 일요일 시작(i=0)으로 올바르게 배치됩니다.
            lbl.grid(row=0, column=i, padx=5, pady=1, sticky="nsew") 

        # Calendar grid container
        # (tk.Frame 대신 ctk.CTkFrame을 사용하여 테마 통일성 유지)
        self.grid_container = ctk.CTkFrame(self.calendar_frame_container, fg_color="transparent") 
        # ⭐ [사이즈 최소화] pady를 (1, 8)로 축소 ⭐
        self.grid_container.pack(fill="both", expand=True, padx=8, pady=(1, 8)) 

        for r in range(7): self.grid_container.rowconfigure(r, weight=1)
        for c in range(7): self.grid_container.columnconfigure(c, weight=1)


        
    def _build_input_form(self):
        
        # ------------------- 상단 고정 영역 -------------------
        top_fixed_frame = ctk.CTkFrame(self.input_frame_container, fg_color="transparent")
        top_fixed_frame.grid(row=0, column=0, sticky="new", padx=0, pady=0)
        top_fixed_frame.grid_columnconfigure(0, weight=1)
        
        date_header_frame = ctk.CTkFrame(top_fixed_frame)
        # ⭐ 수정 1: 상단/하단 패딩을 (10, 5)에서 (5, 2)로 최소화
        date_header_frame.pack(fill="x", padx=10, pady=(5, 2))
        ctk.CTkLabel(date_header_frame, text="📅 Selected Date:", font=ctk.CTkFont(size=14)).pack(side="left", padx=5)
        self.selected_date_label = ctk.CTkLabel(date_header_frame, text=self.selected_date_str, 
                                                 font=ctk.CTkFont(size=16, weight="bold"), text_color="#4FC3F7")
        self.selected_date_label.pack(side="right", padx=5)

        # ⭐ 위젯을 self 변수에 할당하여 다른 메서드에서 접근 가능하도록 함 ⭐
        self.std_time_label = ctk.CTkLabel(top_fixed_frame, text="", text_color="gray")
        # ⭐ 수정 2: std_time_label 하단 패딩 제거 (기존: padx=10)
        self.std_time_label.pack(anchor="w", padx=10, pady=(0, 0))
        

        # ------------------- 스크롤 영역 (중앙 확장) -------------------
        scroll_frame_wrapper = ctk.CTkFrame(self.input_frame_container, fg_color="transparent")
        scroll_frame_wrapper.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        scroll_frame_wrapper.grid_columnconfigure(0, weight=1)
        scroll_frame_wrapper.grid_rowconfigure(0, weight=1)
        
        # 기존: label_text="Check-in Records (HH:MM / WO / PV / CV)"
        scroll_frame = ctk.CTkScrollableFrame(scroll_frame_wrapper, 
                                              label_text="Check-in Records \n(HH:MM / WO / PEL / ANL / HAL / SIL / SPL / EVL)", 
                                              corner_radius=8)

        # ⭐ 수정 3: 스크롤 프레임 자체의 상하 패딩을 5에서 2로 최소화
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=2)
        
        self.entry_vars = {} 
        
        for i, emp in enumerate(self.employees):
            emp_frame = ctk.CTkFrame(scroll_frame)
            # ⭐ 수정 4: 직원별 프레임의 상하 패딩을 5에서 2로 최소화
            emp_frame.pack(fill="x", padx=5, pady=2)

            # (직원명/입력칸은 pady=2로 유지하여 최소한의 간격 확보)
            ctk.CTkLabel(emp_frame, text=f"{emp}").grid(row=0, column=0, padx=5, pady=2, sticky="w")
            
            check_in_var = ctk.StringVar()
            self.entry_vars[f"{emp}_in"] = check_in_var
            ctk.CTkEntry(emp_frame, textvariable=check_in_var, width=120, placeholder_text="HH:MM/Status").grid(row=0, column=1, padx=(10,5), pady=2, sticky="e")
            
            emp_frame.grid_columnconfigure(0, weight=1)
            emp_frame.grid_columnconfigure(1, weight=0)
            
        # 메모 입력란
        ctk.CTkLabel(scroll_frame, text="Memo:").pack(anchor="w", padx=5, pady=(2,0)) # ⭐ 수정 5: 상단 패딩을 (5,0)에서 (2,0)으로 최소화
        self.memo_textbox = ctk.CTkTextbox(scroll_frame, height=60)
        # ⭐ 수정 6: 하단 패딩을 (0, 5)에서 (0, 2)로 최소화
        self.memo_textbox.pack(fill="x", padx=5, pady=(0, 2))

        # 입력 매뉴얼 텍스트
        # (기존 코드에서 pady=(2,0)으로 이미 최소화되어 있어 유지)
        ctk.CTkLabel(scroll_frame, text="[Input Manual]", font=ctk.CTkFont(size=10, weight="bold"), text_color="#AAAAAA").pack(anchor="w", padx=5, pady=(2,0))

        ctk.CTkLabel(scroll_frame, 
                     text="Input Time: HH:MM (e.g. 08:30)\nWO: Work Out\nPEL: Personal Leave\nANL: Annual Leave\nHAL: Half-day Leave\nSIL: Sick Leave\nSPL: Special Leave\nEVL: Event Leave", 
                     font=ctk.CTkFont(size=10), text_color="#FFD700",wraplength=350, justify="left").pack(anchor="w", padx=5, pady=(0,0)) # ⭐ 수정 7: 하단 패딩을 (0,0)으로 제거


    # -------------------------------------------------------
    # ⭐ 1. 폰트와 버튼 높이 정의 (클래스 내부 또는 메서드 상단) ⭐
    # AttendanceCalendarCTK 클래스의 __init__ 메서드 내부에 정의하는 것이 가장 좋습니다.
    self.BUTTON_FONT = ctk.CTkFont(family="Malgun Gothic", size=8, weight="bold")
    self.BUTTON_HEIGHT = 30 # 버튼 높이를 45px로 설정했습니다.
    # -------------------------------------------------------
    
    # ------------------- 하단 고정 영역 -------------------
    # ⭐ 2. 버튼을 하단에 고정하는 프레임 추가 ⭐
    btn_fixed_frame = ctk.CTkFrame(self.input_frame_container, fg_color="transparent")
    # ⭐ 수정 8: 하단 패딩을 10에서 5로 최소화
    btn_fixed_frame.grid(row=2, column=0, sticky="sew", padx=10, pady=5)
    btn_fixed_frame.grid_columnconfigure(0, weight=1)
    btn_fixed_frame.grid_columnconfigure(1, weight=1)
    
    # 💾 Save Record (저장 버튼)
    ctk.CTkButton(
        btn_fixed_frame, 
        text="Save Record", 
        command=self._save_attendance,
        # ⭐ 높이 및 폰트 적용 ⭐ (8칸 들여쓰기)
        height=self.BUTTON_HEIGHT, 
        font=self.BUTTON_FONT
    ).grid(row=0, column=0, sticky="ew", padx=(0, 5))
    
    # 🗑 Delete Record (삭제 버튼)
    ctk.CTkButton(
        btn_fixed_frame, 
        text="Delete Record", 
        fg_color="red", 
        hover_color="#990000", 
        command=self._delete_attendance,
        # ⭐ 높이 및 폰트 적용 ⭐ (8칸 들여쓰기)
        height=self.BUTTON_HEIGHT,
        font=self.BUTTON_FONT
    ).grid(row=0, column=1, sticky="ew", padx=(5, 0))


    // AttendanceView_calendar_ctk.py 파일 내 _update_input_form 메서드 내부

    def _update_input_form(self):
        
        current_std_time = self.data_manager.settings.get("attendance_time")
        self.std_time_label.configure(text=f"Standard Check-in: {current_std_time}")
        
        print(f"[DEBUG:update_form] Searching for data on: {self.selected_date_str}") 

        self.selected_date_label.configure(text=self.selected_date_str)
        
        # 데이터 로드 (이전 단계에서 성공 확인됨)
        day_map = self.data_manager.attendance_data.get(self.selected_date_str, {})
        
        print(f"[DEBUG:update_form] Retrieved data (day_map): {day_map}")
        
        # ⭐ 핵심 수정: 데이터를 입력 폼에 채우는 로직입니다. ⭐
        # 1. 데이터가 존재할 경우: 로드된 데이터로 폼 채우기
        if day_map:
            for key, var in self.entry_vars.items():
                # entry_vars의 key는 직원 이름이며, day_map에서 해당 직원의 근태 상태를 가져옵니다.
                # 데이터가 없으면 'WO' (근무 외)를 기본값으로 설정합니다.
                status_str = day_map.get(key, "WO") 
                var.set(status_str)
            
            # MEMO 필드 채우기
            memo = day_map.get("MEMO", "")
            self.memo_textbox.delete("1.0", "end")
            self.memo_textbox.insert("1.0", memo)
        
        # 2. 데이터가 없을 경우: 폼 초기화 (빈 날짜 클릭 시)
        else:
            # 모든 폼을 'WO' (또는 원하는 초기값)으로 초기화
            for key, var in self.entry_vars.items():
                var.set("WO") 
            
            # MEMO 필드를 비웁니다.
            self.memo_textbox.delete("1.0", "end")
            self.memo_textbox.insert("1.0", "")
            
        # 폼의 상태를 초기화 (필요하다면)
        self._set_input_form_state("normal")


    def _save_attendance(self):
        date_str = self.selected_date_str
        new_day_map = {}
        
        current_std_time = self.data_manager.settings.get("attendance_time")

        try:
            std_time = datetime.strptime(self.attendance_standard_time, '%H:%M').time()
        except ValueError:
             messagebox.showerror("Error", "Attendance standard time in settings is invalid (HH:MM format).")
             return

        for emp in self.employees:
            check_in_input = self.entry_vars[f"{emp}_in"].get().strip().upper()
            
            if not check_in_input: continue 

            if check_in_input in ["WO", "PEL", "ANL", "HAL", "SIL", "SPL", "EVL"]:
                new_day_map[emp] = check_in_input
            
            else:
                try:
                    input_time = datetime.strptime(check_in_input, '%H:%M').time()
                    formatted_time = check_in_input.lstrip('0') 
                    
                    if input_time <= std_time:
                        new_day_map[emp] = f"ATT({formatted_time})"
                    else:
                        new_day_map[emp] = f"LATE({formatted_time})"
                        
                except ValueError:
                    messagebox.showwarning("Warning", f"Input value '{check_in_input}' for {emp} is invalid. (Must be HH:MM, WO, PEL, ANL, HAL, SIL, SPL, or EVL)")
                    continue
        
        memo = self.memo_textbox.get("1.0", "end").strip()
        if memo:
            new_day_map["MEMO"] = memo
            
        if not new_day_map or (len(new_day_map) == 1 and "MEMO" in new_day_map):
            self.data_manager.delete_attendance_record(date_str)
        else:
            self.data_manager.save_attendance_record(date_str, new_day_map)

        self.refresh_records()
        self._draw_calendar()
        self._update_input_form() 
        messagebox.showinfo("Save Complete", f"{date_str} record has been saved.")
        
    def _delete_attendance(self):
        date_str = self.selected_date_str
        
        if not self.attendance_records.get(date_str):
             messagebox.showinfo("Info", f"No record found for {date_str}.")
             return
             
        if messagebox.askyesno("Confirm", f"Are you sure you want to delete all attendance records and memo for {date_str} and update the Excel file?"):
            try:
                self.data_manager.delete_attendance_record(date_str)
                
                self.refresh_records()
                self._draw_calendar()
                self._update_input_form() 
                    
                messagebox.showinfo("Delete Complete", f"{date_str} record has been deleted.")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while deleting the record: {e}")

    # ------------------ 달력/UI 상호작용 ------------------
    def _determine_day_status(self, day_map):
        statuses = [str(v).upper() for k,v in day_map.items() if k!="MEMO"]

        # ⭐ 지각/출석 우선순위 (가장 높음) ⭐
        if any('LATE' in s for s in statuses): return "LATE"
        if any('ATT' in s for s in statuses): return "ATT"
        
        # ⭐ 휴가/외근 우선순위 (나머지 상태) ⭐
        # EVL, SPL, SIL, HAL, ANL, PEL, WO 순으로 우선순위를 설정 (필요에 따라 순서 조정 가능)
        if any('EVL' in s for s in statuses): return "EVL"
        if any('SPL' in s for s in statuses): return "SPL"
        if any('SIL' in s for s in statuses): return "SIL"
        if any('HAL' in s for s in statuses): return "HAL"
        if any('ANL' in s for s in statuses): return "ANL"
        if any('PEL' in s for s in statuses): return "PEL"
        if any('WO' in s for s in statuses): return "WO"
        # 기존 CV, PV는 삭제되었습니다.

        return "NONE"

    def _get_status_from_string(self, status_str):
        if not isinstance(status_str, str): return None
        raw = status_str.upper()
        if raw.startswith('ATT(') or raw == 'ATT': return 'ATT'
        if raw.startswith('LATE(') or raw == 'LATE' : return 'LATE'
        if raw == 'WO': return 'WO'
        # 기존: CV, PV 삭제
        # if raw == 'PV': return 'PV'
        # if raw == 'CV': return 'CV'
        
        # ⭐ 새 상태 추가 ⭐
        if raw == 'PEL': return 'PEL'
        if raw == 'ANL': return 'ANL'
        if raw == 'HAL': return 'HAL'
        if raw == 'SIL': return 'SIL'
        if raw == 'SPL': return 'SPL'
        if raw == 'EVL': return 'EVL'
        
        return None


    
    def _draw_calendar(self):

        """달력 그리드에 날짜와 출석 정보를 그립니다."""

        for widget in self.grid_container.winfo_children():
            widget.destroy()
        
        self.current_highlighted_card = None

        self.title_label.configure(
            text=f"{self.year}년 {self.month:02d}월 출석 기록",
            anchor="center",
            justify="center"
        )

        records = self.attendance_records
        today_str = date.today().strftime("%Y-%m-%d")

        raw_holidays = self.data_manager.settings.get("holidays", {})
        holiday_map = {}
        if isinstance(raw_holidays, dict):
            for h_str, h_name in raw_holidays.items():
                try:
                    d = datetime.strptime(h_str.strip(), '%Y-%m-%d').date()
                    holiday_map[d.strftime('%Y-%m-%d')] = h_name
                except ValueError:
                    pass

        cal = pycal.Calendar(firstweekday=pycal.SUNDAY)
        month_weeks = cal.monthdayscalendar(self.year, self.month)

        for r in range(6):
            week = month_weeks[r] if r < len(month_weeks) else [0] * 7

            for c, day in enumerate(week):
                cell = ctk.CTkFrame(self.grid_container, fg_color=self.CELL_BG, corner_radius=0)
                cell.grid_columnconfigure(0, weight=1)
                cell.grid_rowconfigure(0, weight=1)
                cell.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)

                if day == 0:
                    continue

                day_str = f"{self.year}-{self.month:02d}-{day:02d}"
                day_map = records.get(day_str, {})
                status = self._determine_day_status(day_map)

                cell_bg = self.CELL_BG
                if c == 0:
                    cell_bg = self.SUNDAY_COLOR
                elif c == 6:
                    cell_bg = self.SATURDAY_COLOR

                holiday_name = holiday_map.get(day_str)
                is_holiday = holiday_name is not None
                if is_holiday:
                    cell_bg = self.HOLIDAY_BG

                if day_str == today_str:
                    cell_bg = self.TODAY_BG

                card = ctk.CTkFrame(
                    cell,
                    corner_radius=8,
                    fg_color=cell_bg,
                    border_color="#444444",
                    border_width=1 if status != "NONE" else 0
                )
                card.grid_columnconfigure(0, weight=1)
                card.grid(row=0, column=0, sticky="nsew")

                date_lbl = ctk.CTkLabel(
                    card,
                    text=str(day),
                    anchor="nw",
                    font=self.DATE_FONT,
                    text_color=self.STATUS_COLORS["TEXT"]
                )
                date_lbl.grid(row=0, column=0, sticky="new", padx=6, pady=(6, 0))

                current_row = 1

                if is_holiday:
                    h_lbl = ctk.CTkLabel(
                        card,
                        text=f"🎉 {holiday_name}",
                        anchor="w",
                        font=self.HOLIDAY_FONT,
                        text_color="#FFFFFF"
                    )
                    h_lbl.grid(row=current_row, column=0, sticky="ew", padx=6, pady=(0, 2))
                    current_row += 1

                for emp, status_str in day_map.items():
                    if emp == "__MEMO__":
                        continue

                    core_status = self._get_status_from_string(status_str)
                    line_color = self.STATUS_COLORS.get(core_status, self.STATUS_COLORS["TEXT"])
                    line_text = f"{emp}: {status_str}"

                    lbl = ctk.CTkLabel(
                        card,
                        text=line_text,
                        anchor="w",
                        font=self.CALENDAR_FONT,
                        text_color=line_color,
                        wraplength=self._get_wraplength()    # ★ 수정됨
                    )
                    lbl.grid(row=current_row, column=0, sticky="ew", padx=6, pady=(0, 1))
                    current_row += 1

                if not day_map or (len(day_map) == 1 and "__MEMO__" in day_map):
                    empty_lbl = ctk.CTkLabel(
                        card,
                        text="(no data)",
                        anchor="w",
                        font=ctk.CTkFont(size=9),
                        text_color="#AAAAAA"
                    )
                    empty_lbl.grid(row=current_row, column=0, sticky="ew", padx=6, pady=1)
                    current_row += 1

                if current_row > 1:
                    card.grid_rowconfigure(current_row, weight=1)

                click_handler = lambda e, d=day_str, c=card, b=cell_bg: self._on_day_click(d, c, b)
                card.bind("<Button-1>", click_handler)

                for child in card.winfo_children():
                    child.bind("<Button-1>", click_handler)

                cell.bind("<Button-1>", click_handler)

    def _get_wraplength(self):
        return self.grid_container.winfo_width() // 7 - 12

    def _create_day_cell(self, parent, r, c, day, day_str, day_map, today_str, holiday_map):

        cell_bg = self.CELL_BG
        if c == 0:
            cell_bg = self.SUNDAY_COLOR
        elif c == 6:
            cell_bg = self.SATURDAY_COLOR

        holiday_name = holiday_map.get(day_str)
        is_holiday = holiday_name is not None
        if is_holiday:
            cell_bg = self.HOLIDAY_BG

        if day_str == today_str:
            cell_bg = self.TODAY_BG

        cell = ctk.CTkFrame(parent, fg_color=self.CELL_BG, corner_radius=0)
        cell.grid_columnconfigure(0, weight=1)
        cell.grid_rowconfigure(0, weight=1)
        cell.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)

        card = ctk.CTkFrame(
            cell,
            corner_radius=8,
            fg_color=cell_bg,
            border_color="#444444",
            border_width=1
        )
        card.grid_columnconfigure(0, weight=1)
        card.grid(row=0, column=0, sticky="nsew")

        date_lbl = ctk.CTkLabel(
            card,
            text=str(day),
            anchor="nw",
            font=self.DATE_FONT,
            text_color=self.STATUS_COLORS["TEXT"]
        )
        date_lbl.grid(row=0, column=0, sticky="new", padx=6, pady=(6, 0))

        current_row = 1

        if is_holiday:
            h_lbl = ctk.CTkLabel(
                card,
                text=f"🎉 {holiday_name}",
                anchor="w",
                font=self.HOLIDAY_FONT,
                text_color="#FFFFFF"
            )
            h_lbl.grid(row=current_row, column=0, sticky="ew", padx=6, pady=(0, 2))
            current_row += 1

        for emp, status_str in day_map.items():
            if emp == "__MEMO__":
                continue

            core_status = self._get_status_from_string(status_str)
            line_color = self.STATUS_COLORS.get(core_status, self.STATUS_COLORS["TEXT"])
            line_text = f"{emp}: {status_str}"

            lbl = ctk.CTkLabel(
                card,
                text=line_text,
                anchor="w",
                font=self.CALENDAR_FONT,
                text_color=line_color,
                wraplength=self._get_wraplength()     # ★ 수정됨
            )
            lbl.grid(row=current_row, column=0, sticky="nw", padx=6, pady=(0, 1))
            current_row += 1

        if not day_map or (len(day_map) == 1 and "__MEMO__" in day_map):
            empty_lbl = ctk.CTkLabel(
                card,
                text="(no data)",
                anchor="w",
                font=ctk.CTkFont(size=9),
                text_color="#AAAAAA"
            )
            empty_lbl.grid(row=current_row, column=0, sticky="ew", padx=6, pady=1)
            current_row += 1

        if current_row > 1:
            card.grid_rowconfigure(current_row, weight=1)

        click_handler = lambda e, d=day_str, c=card, b=cell_bg: self._on_day_click(d, c, b)
        card.bind("<Button-1>", click_handler)
        for child in card.winfo_children():
            child.bind("<Button-1>", click_handler)
        cell.bind("<Button-1>", click_handler)



                    
    def _go_to_today(self):
        """현재 날짜로 달력을 이동하고, 해당 날짜를 선택합니다."""
        today = date.today()
        self.year = today.year
        self.month = today.month
        self.selected_date_str = today.strftime("%Y-%m-%d")
        self._draw_calendar()
        self._update_input_form()

    def _prev_month(self):
        self.month -= 1
        if self.month < 1: self.month = 12; self.year -= 1
        self._draw_calendar()

    def _next_month(self):
        self.month += 1
        if self.month > 12: self.month = 1; self.year += 1
        self._draw_calendar()


    # ... (생략) ...

    def _on_day_click(self, day_str, card_widget, original_bg):
        """하이라이트 기능을 포함한 클릭 핸들러입니다."""
        
        # 1. 이전 카드 초기화 및 현재 카드 하이라이트 처리
        
        # 이전 카드가 있고, 현재 클릭한 카드와 다를 경우: 이전 카드 색상 복원
        if self.current_highlighted_card is not None and self.current_highlighted_card != card_widget:
            if hasattr(self.current_highlighted_card, '_original_bg'):
                self.current_highlighted_card.configure(fg_color=self.current_highlighted_card._original_bg)
        
        # 현재 카드가 하이라이트된 카드가 아닐 경우: 하이라이트 적용
        if self.current_highlighted_card != card_widget:
            card_widget.configure(fg_color=self.HIGHLIGHT_BG)
            card_widget._original_bg = original_bg # 원래 배경색 저장
            self.current_highlighted_card = card_widget

        # 2. 입력 폼 업데이트 (필수 데이터 처리)
        # ⭐ 이 부분이 핵심입니다. 클릭 시마다 항상 실행되어야 합니다. ⭐
        self.selected_date_str = day_str

# ⭐ 디버깅 코드 추가: 선택된 날짜 확인 ⭐
        print(f"[DEBUG:on_day_click] Selected Date: {self.selected_date_str}") # ⭐ 이 줄은 반드시 '#' 주석이 아닌 코드로 유지 ⭐

        self._update_input_form() # 이 함수가 호출되면 왼쪽 입력창이 갱신됩니다.