"""
카이로스 트레이딩 애플리케이션 패키지 초기화 및 실행 모듈입니다.
"""
import logging
import os
import sys
from typing import Dict, Any, List, Optional

import streamlit as st

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# 페이지 및 컴포넌트 관련 모듈 임포트
from .pages.login import render_login_page
from .pages.account import render_account_page
from .pages.stocks import render_stocks_page
from .pages.strategy import render as render_strategy_page
from .pages.backtest import render as render_backtest_page

# 전역 설정
APP_TITLE = "KAIROS 트레이딩 시스템"

def initialize_session_state():
    """세션 상태 초기화"""
    # 사용자 인증 관련
    if 'is_authenticated' not in st.session_state:
        st.session_state.is_authenticated = False
    
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    # 현재 페이지
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "login"

def set_page_config():
    """페이지 설정"""
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def render_sidebar():
    """사이드바 렌더링"""
    with st.sidebar:
        st.title(APP_TITLE)
        
        # 페이지 네비게이션
        if st.session_state.is_authenticated:
            pages = {
                "주식 정보": "stocks",
                "매매 전략": "strategy",
                "백테스팅": "backtest",
                "내 계정": "account"
            }
            
            selected_page = st.radio("메뉴", list(pages.keys()))
            st.session_state.current_page = pages[selected_page]
            
            # 로그아웃 버튼
            if st.button("로그아웃"):
                st.session_state.is_authenticated = False
                st.session_state.user = None
                st.session_state.current_page = "login"
                st.rerun()
        else:
            st.info("로그인이 필요합니다.")

def render_current_page():
    """현재 선택된 페이지 렌더링"""
    # 인증 체크
    if not st.session_state.is_authenticated and st.session_state.current_page != "login":
        st.session_state.current_page = "login"
    
    # 페이지 렌더링
    if st.session_state.current_page == "login":
        render_login_page()
    elif st.session_state.current_page == "account":
        render_account_page()
    elif st.session_state.current_page == "stocks":
        render_stocks_page()
    elif st.session_state.current_page == "strategy":
        render_strategy_page()
    elif st.session_state.current_page == "backtest":
        render_backtest_page()
    else:
        st.error("존재하지 않는 페이지입니다.")

def run_app():
    """애플리케이션 실행"""
    try:
        # 페이지 설정
        set_page_config()
        
        # 세션 상태 초기화
        initialize_session_state()
        
        # 개발 모드에서 자동 로그인
        if os.environ.get('KAIROS_DEV_MODE') == '1':
            st.session_state.is_authenticated = True
            st.session_state.user = {'username': 'dev_user', 'name': '개발자', 'account_id': 'dev001'}
            if st.session_state.current_page == 'login':
                st.session_state.current_page = 'stocks'
        
        # 사이드바 렌더링
        render_sidebar()
        
        # 현재 페이지 렌더링
        render_current_page()
        
    except Exception as e:
        logger.exception(f"애플리케이션 실행 중 오류 발생: {e}")
        st.error(f"오류가 발생했습니다: {str(e)}")

# 애플리케이션 실행 진입점
if __name__ == "__main__":
    run_app()
