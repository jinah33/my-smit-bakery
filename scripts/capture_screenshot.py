"""
public/index.html 스크린샷 1회 캡처 스크립트 (screen_design.md 8절 확인 지침 준수)
"""
import os
import sys
import time
import subprocess
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

PORT = 8000

class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="public", **kwargs)
    def log_message(self, format, *args):
        pass  # 조용히 처리

def run_server(httpd):
    httpd.serve_forever()

def capture():
    os.makedirs(os.path.join("results", "screenshots"), exist_ok=True)
    screenshot_path = os.path.abspath(os.path.join("results", "screenshots", "playback_screen.png"))
    
    server_address = ("127.0.0.1", PORT)
    httpd = HTTPServer(server_address, QuietHandler)
    server_thread = threading.Thread(target=run_server, args=(httpd,), daemon=True)
    server_thread.start()
    print(f"로컬 웹 서버 시작됨: http://127.0.0.1:{PORT}")
    time.sleep(1)

    # Edge 또는 Chrome 경로 찾기
    browser_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]
    
    browser_bin = None
    for bp in browser_paths:
        if os.path.exists(bp):
            browser_bin = bp
            break
            
    if not browser_bin:
        print("경고: 브라우저 실행 파일을 찾을 수 없습니다.")
        httpd.shutdown()
        return

    print(f"브라우저 실행 중: {browser_bin}")
    cmd = [
        browser_bin,
        "--headless=new",
        "--virtual-time-budget=3000",
        f"--screenshot={screenshot_path}",
        "--window-size=1280,800",
        "--hide-scrollbars",
        f"http://127.0.0.1:{PORT}/index.html"
    ]
    
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=15)
        print("브라우저 캡처 완료.")
        if os.path.exists(screenshot_path):
            size_kb = os.path.getsize(screenshot_path) / 1024
            print(f"스크린샷 저장 성공: {screenshot_path} ({size_kb:.1f} KB)")
        else:
            print("스크린샷 파일이 생성되지 않았습니다.")
    except Exception as e:
        print(f"스크린샷 캡처 중 오류: {e}")
    finally:
        httpd.shutdown()
        print("로컬 서버 종료됨.")

if __name__ == '__main__':
    capture()
