import customtkinter as ctk # 파일의 첫 줄은 이 코드가 되어야 합니다.
import json
import os
from tkinter import messagebox
import requests # ⭐ 이 줄을 추가해야 합니다! ⭐

class ExchangeRateViewer(ctk.CTkFrame):
    """
    환율 정보를 표시하는 뷰입니다.
    데이터는 외부 JSON 파일 또는 API를 통해 로드될 수 있습니다.
    """
    # 기준 통화는 USD로 고정됩니다.
    API_URL = "https://open.er-api.com/v6/latest/USD"
    
    # 표시할 주요 통화 (요청 사항 반영)
    TARGET_CURRENCIES = [
        "USD", "KRW", "IDR", "JPY", "EUR", 
        "CNY", "GBP", "CAD", "AUD", "SGD"
    ]
    
    # 통화 코드를 한글 이름으로 매핑 (선택 사항)
    CURRENCY_NAMES = {
        "USD": "US Dollar", 
        "KRW": "South Korean Won", 
        "IDR": "Indonesian Rupiah",
        "JPY": "Japanese Yen", 
        "EUR": "Euro", 
        "CNY": "Chinese Yuan",
        "GBP": "British Pound", 
        "CAD": "Canadian Dollar", 
        "AUD": "Australian Dollar",
        "SGD": "Singapore Dollar"
    }

    def __init__(self, master):
        super().__init__(master, corner_radius=10, fg_color="transparent")
        self.rates = {} # 환율 데이터 저장 딕셔너리
        
        self.grid_columnconfigure(0, weight=1)
        
        self._build_ui()
        self.load_rates_data()

    def _build_ui(self):
        # 헤더
        ctk.CTkLabel(
            self, 
            text="💰 Exchange rate information for major countries (based on USD)", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=5, pady=(10, 5), sticky="nw")
        
        # 이렇게 하면 프레임 자체에 고정된 height를 적용하기 쉽습니다.
        self.rate_display_frame = ctk.CTkScrollableFrame(
            self, 
            fg_color="gray25",
            height=160 # 예시로 180px 설정 (전체 뷰 height=200px에 맞게 내부 높이 조정)
        )
        self.rate_display_frame.grid(row=1, column=0, padx=5, pady=(0, 10), sticky="ew")
        # 스크롤 가능한 프레임 내부의 레이아웃 설정
        self.rate_display_frame.grid_columnconfigure(0, weight=1)
        self.rate_display_frame.grid_columnconfigure(1, weight=1)

        # 상태 표시 레이블
        self.status_label = ctk.CTkLabel(
            self, 
            text="Status: Loading data...", 
            font=ctk.CTkFont(size=11, slant="italic"),
            anchor="w"
        )
        self.status_label.grid(row=2, column=0, padx=5, pady=(5, 5), sticky="ew")

# exchange_rate_viewer.py (load_rates_data 메서드)

    def load_rates_data(self):
        """
        ExchangeRate-API의 무료 엔드포인트를 호출하여 환율 데이터를 로드합니다.
        """
        self.status_label.configure(text="Status: Loading exchange rate data...", text_color="yellow")

        try:
            # 1. API 호출
            # requests 라이브러리가 설치되어 있어야 합니다 (pip install requests)
            response = requests.get(self.API_URL, timeout=10) 
            response.raise_for_status() # HTTP 오류 발생 시 예외 처리

            data = response.json()
            
            # 2. 데이터 유효성 검사 및 저장
            if data.get('result') == 'success' and 'rates' in data:
                self.rates = data['rates']
                update_time = data.get('time_last_update_utc', 'No time information')
                
                status_text = f"Status: {data.get('base', 'USD')} based on, {update_time} Updated"

                self.status_label.configure(text=status_text, text_color="white")
            else:
                raise ValueError(f"API response failed or was in a different format than expected: {data.get('error-type', 'unknown')}")

        except requests.exceptions.RequestException as e:
            # "API 호출 중 네트워크 오류가 발생했습니다. 인터넷 연결을 확인하세요: {e}"
            messagebox.showerror("Network Error", f"A network error occurred during the API call. Please check your internet connection: {e}")
            
            # "상태: 네트워크 오류"
            self.status_label.configure(text="Status: Network Error", text_color="red")
            return
        
        except ValueError as e:
            # "환율 데이터 처리 오류: {e}"
            messagebox.showerror("Data Error", f"Currency data processing error: {e}")
            
            # "상태: 데이터 처리 오류"
            self.status_label.configure(text="Status: Data Processing Error", text_color="red")
            return
        
        except Exception as e:
            # "예기치 않은 오류가 발생했습니다: {e}"
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            
            # "상태: 알 수 없는 오류"
            self.status_label.configure(text="Status: Unknown Error", text_color="red")
            return            
        # 3. UI 업데이트
        self._update_display()

        
    def _update_display(self):
        """로드된 환율 데이터를 UI에 표시합니다."""
        # 기존 위젯 제거
        for widget in self.rate_display_frame.winfo_children():
            widget.destroy()
            
        row = 0
        for currency in self.TARGET_CURRENCIES:
            if currency in self.rates:
                rate = self.rates[currency]
                name = self.CURRENCY_NAMES.get(currency, currency)
                
                # 통화 이름 (좌측)
                ctk.CTkLabel(
                    self.rate_display_frame, 
                    text=f"{name} ({currency})", 
                    anchor="w"
                ).grid(row=row, column=0, padx=10, pady=3, sticky="w")
                
                # 환율 값 (우측)
                ctk.CTkLabel(
                    self.rate_display_frame, 
                    text=f"{rate:,.2f}", # 소수점 둘째 자리, 쉼표 구분
                    anchor="e",
                    font=ctk.CTkFont(weight="bold")
                ).grid(row=row, column=1, padx=10, pady=3, sticky="e")
                
                row += 1
