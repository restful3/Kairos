#!/usr/bin/env python
import os
import sys
from pathlib import Path

# 현재 스크립트 경로
current_path = Path(__file__).parent.absolute()

# 상위 디렉토리를 파이썬 경로에 추가
parent_path = current_path.parent
sys.path.insert(0, str(parent_path))

# Streamlit 프론트엔드 실행
if __name__ == "__main__":
    import streamlit.web.bootstrap
    
    # 메인 모듈 경로
    main_script = os.path.join(current_path, "app", "main.py")
    
    # 실행 인자
    args = []
    
    # 포트 설정 (기본값: 8501)
    if "--port" not in sys.argv:
        args.extend(["--server.port", "8501"])
    
    # 브라우저 자동 열기 비활성화
    if "--no-browser" not in sys.argv:
        args.extend(["--server.headless", "true"])
    
    # 실행 명령
    sys.argv = [sys.argv[0]] + args + sys.argv[1:]
    
    # Streamlit 실행
    streamlit.web.bootstrap.run(main_script, "", args, flag_options={}) 