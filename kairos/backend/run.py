"""
Kairos 백엔드 서버 실행 스크립트
"""
import os
import sys
import logging
import uvicorn
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """백엔드 서버를 실행합니다."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "True").lower() in ("true", "1", "t")
    
    logger.info(f"서버를 시작합니다 (host={host}, port={port}, reload={reload})")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload
    )

if __name__ == "__main__":
    main() 