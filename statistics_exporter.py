import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import os
from datetime import datetime, date
import calendar as pycal 
import io

# ReportLab PDF 생성을 위한 라이브러리 유지
from reportlab.lib.pagesizes import A4, landscape 
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.pdfmetrics import registerFont, registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont

# xlsxwriter 엔진 사용을 위한 import
import xlsxwriter 

# ----------------------------------------------------
# ⭐ 폰트 및 Matplotlib 설정 (PDF 보고서 한글 지원을 위해 유지) ⭐
# 웹 서버 환경에 따라 FONT_PATH는 다를 수 있습니다. (배포 시 서버에 폰트 파일 포함 필수)
matplotlib.use("Agg")  # GUI 백엔드 비활성화
matplotlib.rc('font', family='Malgun Gothic') 
matplotlib.rcParams['axes.unicode_minus'] = False

# 웹 환경에서는 폰트 경로를 상대 경로로 관리하는 것이 좋습니다.
# 여기서는 윈도우 경로를 유지하되, 경고 처리 추가
FONT_PATH = "C:\\Windows\\Fonts\\malgun.ttf" 
KOREAN_FONT = 'Helvetica' # 기본값

try:
    if os.path.exists(FONT_PATH):
        registerFont(TTFont('KoreanFont', FONT_PATH)) 
        registerFontFamily('KoreanFont', normal='KoreanFont', bold='KoreanFont')
        KOREAN_FONT = 'KoreanFont'
    else:
        print(f"[WARNING] MalgunGothic font file not found. Using default font for PDF.")
except Exception as e:
    print(f"[ERROR] Failed to register Korean font: {e}")

# 근태 상태 상수 (data_manager와 동기화)
ALL_STATUS_COLS = ["ATT", "LATE", "WO", "PEL", "ANL", "HAL", "SIL", "SPL", "EVL"]
LEAVE_COLS = ["PEL", "ANL", "HAL", "SIL", "SPL", "EVL"]
STATUS_COLORS = {
    "ATT": "#4FC3F7", "LATE": "#F44336", "WO": "#FFFFFF", 
    "PEL": "#FFC107", "ANL": "#00BCD4", "HAL": "#8BC34A", 
    "SIL": "#9C27B0", "SPL": "#FF5722", "EVL": "#607D8B"
}
# ----------------------------------------------------

class StatisticsExporter:
    """통계 데이터 내보내기 (PDF, Excel) 로직을 전담합니다."""
    
    def __init__(self, data_manager):
        # DataManager 객체를 주입받아 통계 데이터를 계산합니다.
        self.data_manager = data_manager

    def _get_df_for_period(self, report_type, year, month=None):
        """지정된 기간의 통계 데이터프레임을 DataManager로부터 가져옵니다."""
        
        start_date = None
        end_date = None
        title = ""
        is_total = (report_type == "total")
        
        if report_type == "monthly":
            _, last_day = pycal.monthrange(year, month)
            start_date = date(year, month, 1)
            end_date = date(year, month, last_day)
            title = f"{year} - {month} M Attendance statistics"
        
        elif report_type == "yearly":
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
            title = f"{year} Attendance statistics"
        
        elif report_type == "total":
             title = "Attendance statistics for the entire period"

        # DataManager의 calculate_statistics 메서드 호출
        df = self.data_manager.calculate_attendance_stats(
            start_date=start_date.strftime('%Y-%m-%d') if start_date else None, 
            end_date=end_date.strftime('%Y-%m-%d') if end_date else None,
            is_total=is_total
        )
        
        return df, title, start_date, end_date

    def create_attendance_chart(self, df, chart_title, figsize=(10, 5)):
        """
        [GUI 독립] 통계 데이터프레임으로 Matplotlib 막대 그래프를 생성하고 Figure 객체를 반환합니다.
        (기존 attendance_statistics_ctk.py의 _plot_chart 메서드 로직)
        """
        
        if df.empty or 'Employee' not in df.columns:
            # 빈 Figure 반환
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, "No data available", ha='center', va='center', fontsize=12)
            return fig
            
        # Employee 컬럼을 제외한 통계 컬럼만 선택
        plot_cols = [col for col in ALL_STATUS_COLS if col in df.columns]

        # Matplotlib Figure 생성
        fig, ax = plt.subplots(figsize=figsize)
        
        # 바 차트 생성 (stacked=True 제거됨, 막대 카운트 표시 로직 추가됨)
        # 웹 환경에서는 Dark Mode 컬러 대신 기본 Plotly를 사용할 수 있지만, 
        # PDF 출력을 위해 Matplotlib의 스타일을 유지합니다.
        
        df_plot = df.set_index('Employee')[plot_cols]
        df_plot.plot(kind='bar', stacked=False, ax=ax, color=[STATUS_COLORS.get(col, '#CCCCCC') for col in plot_cols])

        # 그래프 제목 및 축 라벨 설정
        ax.set_title(chart_title, color='black', fontsize=12, fontweight='bold', fontproperties=matplotlib.font_manager.FontProperties(fname=FONT_PATH))
        ax.set_xlabel("Employee", color='black')
        ax.set_ylabel("Count", color='black')

        # 기타 스타일 조정 (PDF 출력을 위해 Dark Mode 스타일은 제거)
        ax.tick_params(colors='black', axis='x', rotation=0, labelsize=8)
        ax.tick_params(colors='black', axis='y', labelsize=9)
        
        for label in ax.get_xticklabels():
            label.set_fontweight('bold')

        # 범례 폰트 및 스타일 조정 (PDF에 맞춰 축소)
        legend_props = {'weight':'bold', 'size':7} 
        ax.legend(loc='upper right', prop=legend_props, handlelength=0.5)

        # 막대 그래프 상단에 숫자 카운터 표시 (PDF 가독성을 위해 필수)
        for container in ax.containers:
            ax.bar_label(container, label_type='edge', color='black', fontsize=8)
        
        # y축의 범위 조정
        max_val = df_plot.sum(axis=1).max()
        ax.set_ylim(0, max_val * 1.2 if max_val > 0 else 10) 

        plt.tight_layout()
        
        return fig # Figure 객체 반환

    def generate_pdf_summary(self, file_path, report_type, year, month=None):
        """월별 또는 년별 통계 리포트를 PDF로 내보냅니다. (파일 경로는 필수 인자)"""
        
        df, title_ko, _, _ = self._get_df_for_period(report_type, year, month)
        
        if df.empty:
            raise Exception(f"No data available for the period: {title_ko}.")

        # ⭐ PDF 내보내기 제목 영문화 (기존 로직 유지) ⭐
        if report_type == 'monthly' and month:
            title_en = f"Attendance Report - {year}-{month:02d}"
        elif report_type == 'yearly':
            title_en = f"Attendance Report - {year}"
        else:
            title_en = f"Attendance Report - All Time"

        # 1. Matplotlib 차트 생성 및 메모리(BytesIO)에 저장
        # PDF 인쇄를 위해 figsize 조정
        fig = self.create_attendance_chart(df.copy(), title_en, figsize=(10, 5)) 
        
        img_data = io.BytesIO()
        fig.savefig(img_data, format='png', bbox_inches='tight', dpi=150)
        img_data.seek(0)
        plt.close(fig) # Figure 닫기
        
        # 2. ReportLab PDF 문서 생성
        doc = SimpleDocTemplate(file_path, pagesize=landscape(A4),
                                 leftMargin=30, rightMargin=30, 
                                 topMargin=30, bottomMargin=30)
        
        # 영문 스타일 정의
        heading_style = ParagraphStyle(
            name='Heading1', fontSize=16, leading=20, fontName=KOREAN_FONT, alignment=0 
        )
        data_header_style = ParagraphStyle(
            name='DataHeader', fontSize=11, leading=14, fontName=KOREAN_FONT, alignment=1 
        )
        summary_body_style = ParagraphStyle(
            name='SummaryBody', fontSize=10, leading=14, fontName=KOREAN_FONT, alignment=0 
        )
        
        # 3. PDF 요소 구성
        elements = []
        
        # 제목
        elements.append(Paragraph(f"<b>{title_en}</b>", heading_style))
        elements.append(Spacer(1, 12))
        
        # 데이터 요약 테이블
        summary_df = df.copy()
        data_cols_order = ALL_STATUS_COLS
        data_cols = [col for col in data_cols_order if col in summary_df.columns]
        data = [["Employee"] + data_cols] 
        
        for index, row in summary_df.iterrows():
            row_data = [row['Employee']]
            for col in data_cols:
                count = int(row.get(col, 0))
                row_data.append(str(count) if count > 0 else '-')
            data.append(row_data)

        # ReportLab Table 스타일 (다크 모드 색상은 제거하고 밝은 색상 유지)
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4FC3F7")), 
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), KOREAN_FONT),  # ✅ 여기 수정
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#E0E0E0")), 
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ])

        col_widths = [120] + [60] * len(data_cols)
        table = Table(data, colWidths=col_widths)
        table.setStyle(table_style)
        
        elements.append(Paragraph(f"<b>Summary ({len(df)} Employees)</b>", data_header_style)) 
        elements.append(Spacer(1, 6))
        elements.append(table)
        elements.append(Spacer(1, 12)) 
        
        # 직원별 상세 요약 생성 로직 (영문으로 변경된 로직 유지)
        elements.append(Paragraph(f"<b>Per-Employee Detailed Summary</b>", data_header_style))
        elements.append(Spacer(1, 6))

        for index, row in summary_df.iterrows():
            employee_name = row['Employee']
            existing_cols = [col for col in ALL_STATUS_COLS if col in summary_df.columns]
            total_days = row[existing_cols].sum()
            att_count = row.get('ATT', 0)
            late_count = row.get('LATE', 0)
            wo_count = row.get('WO', 0)
            total_leave_count = row[[col for col in LEAVE_COLS if col in summary_df.columns]].sum()
            
            if total_days > 0:
                att_rate = (att_count / total_days) * 100
                late_rate = (late_count / total_days) * 100 
            else:
                att_rate = 0
                late_rate = 0
                
            summary_text = (
                f"<b>{employee_name}:</b> "
                f"Attendance Rate <b>{att_rate:.1f}%</b>, "
                f"Lateness <b>{int(late_count)} times</b>, "
                f"Work Outside <b>{int(wo_count)} times</b>, "
                f"Total Leave ({len(LEAVE_COLS)} types) <b>{int(total_leave_count)} days</b>."
            )
            elements.append(Paragraph(summary_text, summary_body_style))

        elements.append(Spacer(1, 24))
        
        # 차트 이미지
        chart_width = 720 # 가로 용지에 맞춤
        chart_height = 400 
        elements.append(Paragraph("<b>Per-Employee Attendance Chart</b>", heading_style)) 
        elements.append(Spacer(1, 12))
        
        chart_image = Image(img_data, width=chart_width, height=chart_height)
        chart_image.hAlign = 'CENTER'
        elements.append(chart_image)
        
        # 4. PDF 빌드
        doc.build(elements)
            
    def export_excel_report(self, file_path, report_type, year, month=None):
        """[GUI 독립] 통계 데이터와 차트를 Excel 파일로 내보냅니다. (파일 경로는 필수 인자)"""
        
        df, title_ko, _, _ = self._get_df_for_period(report_type, year, month)
        
        if df.empty:
            raise Exception(f"No data to export for the period: {title_ko}.")

        try:
            # 1. Matplotlib 그림을 임시 파일로 저장
            fig = self.create_attendance_chart(df.copy(), title_ko, figsize=(8, 5))
            img_path = 'temp_chart.png'
            fig.savefig(img_path)
            plt.close(fig) 

            # 2. ExcelWriter를 xlsxwriter 엔진으로 생성 및 데이터 저장
            writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
            sheet_name = 'Attendance Stats'
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]

            # 3. 엑셀 시트에 이미지 삽입 (G2 셀에 삽입)
            worksheet.insert_image('G2', img_path) 

            # 4. ExcelWriter 닫기 (파일 저장)
            writer.close()
            
            # 5. 임시 이미지 파일 삭제
            os.remove(img_path)
            
        except Exception as e:
            if os.path.exists('temp_chart.png'):
                os.remove('temp_chart.png')
            raise Exception(f"Excel export error: {e}")