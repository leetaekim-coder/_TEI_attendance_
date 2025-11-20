import customtkinter as ctk
# StatisticsExporter가 statistics_exporter.py에 있다면, 여기서 임포트합니다.
from statistics_exporter import StatisticsExporter

from datetime import date
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
from tkinter import messagebox, filedialog
import os
import calendar as pycal # 월/년 날짜 계산을 위해 추가

# PDF 생성을 위한 라이브러리 추가
from reportlab.lib.pagesizes import A4, landscape # landscape가 추가되어야 합니다.

from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import registerFont, registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
import io

import matplotlib
matplotlib.use("Agg")  # GUI 백엔드 비활성화

# 폰트 설정 (Windows 기준)
matplotlib.rc('font', family='Malgun Gothic') 
matplotlib.rcParams['axes.unicode_minus'] = False

FONT_PATH = "C:\\Windows\\Fonts\\malgun.ttf"
KOREAN_FONT = 'Helvetica' # 기본값

try:
    if os.path.exists(FONT_PATH):
        registerFont(TTFont('KoreanFont', FONT_PATH)) 
        registerFontFamily('KoreanFont', normal='KoreanFont', bold='KoreanFont')
        KOREAN_FONT = 'KoreanFont'
    else:
        # 폰트 파일을 찾지 못하면 Helvetica를 대체로 사용 (한글 깨짐 발생)
        KOREAN_FONT = 'Helvetica' 
        print(f"[WARNING] MalgunGothic font file not found at {FONT_PATH}. Using default font for PDF.")
except Exception as e:
    KOREAN_FONT = 'Helvetica'
    print(f"[ERROR] Failed to register Korean font: {e}")


BG_COLOR = "#2E2E2E"
TEXT_BG_COLOR = "#1E1E1E"

# attendance_statistics_ctk.py 파일 내, StatisticsViewCTK 클래스 위에 다음 내용을 추가합니다.

# ----------------------------------------------------------------------
# class StatisticsExporter: 
#     """(StatisticsExporter 클래스는 변경 없음. 단, 아래 두 메서드가 필요함)"""
#     def _get_df_for_period(self, period_type, year, month): 
#         # 실제 구현에서는 pandas DataFrame과 한국어 제목을 반환합니다.
#         return pd.DataFrame(), "제목", None, None 
#     
#     def create_attendance_chart(self, df, title_ko, figsize): 
#         # 실제 구현에서는 matplotlib Figure 객체를 반환합니다.
#         return plt.figure(figsize=figsize)
# ----------------------------------------------------------------------


class StatisticsViewCTK(ctk.CTkFrame):
    
    # ⭐ MODIFIED: 통계 화면이 선택 없이 3가지 통계를 모두 표시하도록 구조 변경 ⭐
    def __init__(self, master, data_manager, statistics_exporter):
        super().__init__(master, corner_radius=10)
        self.data_manager = data_manager
        self.statistics_exporter = statistics_exporter
        
        # Matplotlib 캔버스 및 Figure 저장 리스트 초기화
        self.chart_canvases = []
        self.chart_figures = []
        
        # 1. Grid Layout Configuration (수직으로 3개 섹션 배치)
        self.grid_columnconfigure(0, weight=1)
        # 월간(0), 연간(1), 전체(2) 섹션에 동일한 높이 가중치를 부여합니다.
        self.grid_rowconfigure((0, 1, 2), weight=1) 

        # 2. 통계 결과를 표시할 세 개의 섹션 프레임 생성 (fg_color를 #1E1E1E로 명시)
        
        # 2-1. 월간 통계 섹션
        self.monthly_section = ctk.CTkFrame(self, corner_radius=10, fg_color="#1E1E1E")
        self.monthly_section.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="nsew")
        self.monthly_section.grid_columnconfigure(0, weight=1)
        self.monthly_section.grid_rowconfigure(1, weight=1) # 차트 프레임에 가중치 부여
        
        self.monthly_section_label = ctk.CTkLabel(self.monthly_section, text="월간 통계 (이번 달)", font=ctk.CTkFont(size=14, weight="bold"))
        self.monthly_section_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        self.monthly_chart_frame = ctk.CTkFrame(self.monthly_section, fg_color="transparent") # 차트를 그릴 프레임
        self.monthly_chart_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        # 2-2. 연간 통계 섹션
        self.yearly_section = ctk.CTkFrame(self, corner_radius=10, fg_color="#1E1E1E")
        self.yearly_section.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.yearly_section.grid_columnconfigure(0, weight=1)
        self.yearly_section.grid_rowconfigure(1, weight=1)
        
        self.yearly_section_label = ctk.CTkLabel(self.yearly_section, text="연간 통계 (이번 년도)", font=ctk.CTkFont(size=14, weight="bold"))
        self.yearly_section_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        self.yearly_chart_frame = ctk.CTkFrame(self.yearly_section, fg_color="transparent") # 차트를 그릴 프레임
        self.yearly_chart_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        # 2-3. 전체 통계 섹션
        self.overall_section = ctk.CTkFrame(self, corner_radius=10, fg_color="#1E1E1E")
        self.overall_section.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="nsew")
        self.overall_section.grid_columnconfigure(0, weight=1)
        self.overall_section.grid_rowconfigure(1, weight=1)
        
        self.overall_section_label = ctk.CTkLabel(self.overall_section, text="전체 기간 통계", font=ctk.CTkFont(size=14, weight="bold"))
        self.overall_section_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        self.overall_chart_frame = ctk.CTkFrame(self.overall_section, fg_color="transparent") # 차트를 그릴 프레임
        self.overall_chart_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        # 초기 통계 표시
        self.refresh_stats()


    def _clear_charts(self):
        for fig in self.chart_figures:
            plt.close(fig)
        for canvas in self.chart_canvases:
            canvas.get_tk_widget().destroy()
        # 기존 chart_display_frame 제거 대신 3개 프레임 모두 초기화
        for frame in [self.monthly_chart_frame, self.yearly_chart_frame, self.overall_chart_frame]:
            for widget in frame.winfo_children():
                widget.destroy()
        self.chart_canvases = []
        self.chart_figures = []



    def _display_chart(self, chart_frame, df, title_ko, period_type):
        """데이터를 기반으로 차트를 생성하고 지정된 프레임에 표시합니다."""
        
        # chart_frame의 위젯을 여기서 제거할 필요는 없습니다. 
        # _clear_charts에서 전체를 제거하고, refresh_stats가 각 차트를 새로운 프레임에 그리도록 설계하는 것이 일반적입니다.

        # --- (코드 흐름 확인) ---
        if df.empty:
            ctk.CTkLabel(chart_frame, text=f"표시할 데이터가 없습니다. ({title_ko})", text_color="gray").pack(expand=True, fill="both")
            return
            
        try:
            # StatisticsExporter의 create_attendance_chart 호출
            fig = self.statistics_exporter.create_attendance_chart(df.copy(), title_ko, figsize=(5, 3)) 
        except Exception as e:
            ctk.CTkLabel(chart_frame, text=f"차트 생성 오류: {e}", text_color="red").pack(expand=True, fill="both")
            return

        # Matplotlib 차트를 CustomTkinter에 임베드
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas_widget = canvas.get_tk_widget()
        # ⭐ 핵심: 캔버스 위젯이 프레임 내부에 완전히 채워지도록 설정 확인 ⭐
        canvas_widget.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        canvas.draw()
        
        # 메모리 관리를 위해 저장
        self.chart_canvases.append(canvas)
        self.chart_figures.append(fig)


    def refresh_stats(self):
        """
        통계 탭 진입 시 자동으로 월간, 연간, 전체 통계를 모두 표시합니다.
        """
        # 1. 기존 차트 삭제
        self._clear_charts() # 명시적으로 캔버스 위젯까지 제거하도록 _clear_charts 수정

        # 2. 현재 날짜 기준으로 통계 계산 및 표시
        today = date.today()
        year = today.year
        month = today.month

        # 월간 통계
        self._display_chart(
                self.monthly_chart_frame,
                self.data_manager.calculate_attendance_stats('month', year, month),
                f"{year}년 {month}월 통계", 'month'
        )

        # 연간 통계
        self._display_chart(
                self.yearly_chart_frame,
                self.data_manager.calculate_attendance_stats('year', year),
                f"{year}년 연간 통계", 'year'
        )

        # 전체 통계
        self._display_chart(
                self.overall_chart_frame,
                self.data_manager.calculate_attendance_stats('all'),
                "전체 기간 통계", 'all'
        )


    def _draw_stats_in_frame(self, period_type, chart_frame):
        """특정 기간의 통계를 계산하고 주어진 프레임에 차트를 그립니다."""
        
        today = date.today()
        year = today.year
        month = today.month

        # 기간 유형에 따라 계산 인자 설정
        calc_year = year if period_type in ['yearly', 'monthly'] else None
        calc_month = month if period_type == 'monthly' else None

        # StatisticsExporter를 통해 데이터프레임 및 제목 가져오기
        try:
            # statistics_exporter.py에 정의된 _get_df_for_period 메서드를 호출
            df, title_ko, _, _ = self.statistics_exporter._get_df_for_period(period_type, calc_year, calc_month)
        except Exception as e:
            ctk.CTkLabel(chart_frame, text=f"데이터 로드 오류: {e}", text_color="red").pack(expand=True, fill="both")
            return
            
        # 기존 위젯 제거 (만약을 대비)
        for widget in chart_frame.winfo_children():
            widget.destroy()

        if df.empty:
            ctk.CTkLabel(chart_frame, text=f"표시할 데이터가 없습니다. ({title_ko})", text_color="gray").pack(expand=True, fill="both")
            return
            
        # 차트 생성 (StatisticsExporter의 create_attendance_chart 재사용)
        try:
            # 3가지 통계를 동시에 보여주기 위해 차트 크기를 작게 조정 (figsize=(5, 3))
            fig = self.statistics_exporter.create_attendance_chart(df.copy(), title_ko, figsize=(5, 3)) 
        except Exception as e:
            ctk.CTkLabel(chart_frame, text=f"차트 생성 오류: {e}", text_color="red").pack(expand=True, fill="both")
            return

        # Matplotlib 차트를 CustomTkinter에 임베드
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        canvas.draw()
        
        # 메모리 관리를 위해 저장
        self.chart_canvases.append(canvas)
        self.chart_figures.append(fig)



