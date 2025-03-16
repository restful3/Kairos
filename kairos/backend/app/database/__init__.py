"""
데이터베이스 패키지 초기화 모듈입니다.
"""
import logging
from .database import db

logger = logging.getLogger(__name__)

def create_tables():
    """
    필요한 데이터베이스 테이블을 생성합니다.
    """
    logger.info("데이터베이스 테이블 초기화 중...")
    db._initialize_db()
    logger.info("데이터베이스 테이블 초기화 완료") 