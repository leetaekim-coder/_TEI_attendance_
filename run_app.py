# run_app.py

import subprocess
import sys
import os

APP_FILE = 'app.py'

def run_streamlit_app():
    cmd = [
        sys.executable,
        "-m", "streamlit", "run",
        APP_FILE,
        "--server.port", "8501", 
        "--browser.gatherUsageStats", "False",
    ]
    
    print(f"Executing command: {' '.join(cmd)}")
    
    # ⭐ subprocess.call 대신 Popen 사용 및 오류 출력을 stderr로 리디렉션 ⭐
    try:
        # Popen을 사용하여 서브프로세스를 시작합니다.
        # stderr=subprocess.PIPE를 사용하여 오류 출력을 캡처할 수 있습니다.
        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True)
        # 서브프로세스가 완료될 때까지 기다리고(이 경우 Streamlit 서버가 종료될 때까지),
        # 오류가 발생하면 stderr를 확인합니다.
        
        # Streamlit 서버는 일반적으로 계속 실행되므로, 이 코드는 간단한 실행을 위해 사용합니다.
        # 실행 후 바로 닫히는 것을 방지하기 위해 간단히 process.wait()을 사용합니다.
        process.wait() 

    except Exception as e:
        print(f"\n--- FATAL ERROR ---")
        print(f"Failed to launch Streamlit subprocess: {e}")
        # 오류가 발생하면 콘솔이 바로 닫히지 않도록 사용자 입력을 기다립니다.
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    run_streamlit_app()