import streamlit as st
import os
from dotenv import load_dotenv

from app.utils.session import init_session_state, is_logged_in
from app.pages.login import show as show_login
from app.pages.account import show as show_account
from app.pages.stocks import show as show_stocks
from app.pages.strategy_builder import show as show_strategy_builder
from app.pages.backtest import show as show_backtest

# 환경 변수 로드
load_dotenv()

def main():
    """메인 함수"""
    
    # 페이지 설정
    st.set_page_config(
        page_title="Kairos - 실시간 퀀트 트레이딩 플랫폼",
        page_icon="⏱️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 세션 초기화
    init_session_state()
    
    # 페이지 자동 이동 처리
    page_to_navigate = st.session_state.get("page", None)
    if page_to_navigate and is_logged_in():
        # 페이지 이동 후 상태 초기화
        current_page = page_to_navigate
        del st.session_state.page
        
        # 메뉴 선택 상태 업데이트
        if current_page == "백테스팅":
            st.session_state.menu_index = 3  # 백테스팅 메뉴 인덱스
        elif current_page == "전략 생성":
            st.session_state.menu_index = 2  # 전략 생성 메뉴 인덱스
        else:
            st.session_state.menu_index = 0  # 기본 메뉴 인덱스
    
    # 항상 현재 메뉴 인덱스 설정 (이전 상태 유지 또는 기본값)
    current_menu_index = st.session_state.get("menu_index", 0)
    
    # 사이드바 메뉴
    with st.sidebar:
        st.title("Kairos")
        st.caption("실시간 퀀트 트레이딩 플랫폼")
        st.divider()
        
        # 로그인 상태에 따라 메뉴 표시
        if is_logged_in():
            # 네비게이션 메뉴
            menu_options = ["계좌 정보", "종목 검색", "전략 생성", "백테스팅", "거래 내역", "도움말"]
            
            # 메뉴 선택
            menu = st.radio(
                "메뉴",
                options=menu_options,
                index=current_menu_index
            )
            
            # 메뉴 선택 상태 저장
            st.session_state.menu_index = menu_options.index(menu)
            
            # 로그아웃 버튼
            if st.button("로그아웃", use_container_width=True):
                from app.utils.session import clear_session
                from app.api.client import api_client
                
                # 세션 및 토큰 정보 삭제
                api_client.logout()
                clear_session()
                st.rerun()
        else:
            # 로그인이 필요한 경우
            menu = "로그인"
            st.info("서비스를 이용하려면 로그인이 필요합니다.")
    
    # 선택한 메뉴에 따라 페이지 표시
    if menu == "로그인" or not is_logged_in():
        show_login()
    elif menu == "계좌 정보":
        show_account()
    elif menu == "종목 검색":
        show_stocks()
    elif menu == "전략 생성":
        show_strategy_builder()
    elif menu == "백테스팅":
        show_backtest()
    elif menu == "거래 내역":
        st.title("거래 내역")
        st.info("거래 내역 페이지는 개발 중입니다.")
    elif menu == "도움말":
        st.title("도움말")
        st.markdown("""
        ## Kairos 플랫폼 사용법
        
        Kairos(그리스어로 '적절한 시기')는 한국투자증권 API를 활용하여 자동화된 주식 거래를 지원하는 플랫폼입니다.
        
        ### 사용 방법
        1. 로그인 페이지에서 사용자 아이디와 비밀번호를 입력합니다.
        2. 계좌 정보 페이지에서 현재 보유 주식과 잔고를 확인합니다.
        3. 종목 검색 페이지에서 투자할 종목을 검색하고 포트폴리오에 추가합니다.
        4. 자동 매매 설정 페이지에서 자동 매매 규칙을 설정합니다.
        5. 거래 내역 페이지에서 과거 거래 내역을 확인합니다.
        
        ### 주의사항
        - 실제 자산이 거래되므로 신중하게 사용하세요.
        - 계정 정보는 타인에게 노출되지 않도록 주의하세요.
        - 시장 상황에 따라 거래가 지연될 수 있습니다.
        
        ### 계정 관련 문의
        - 계정 생성이나 비밀번호 변경은 관리자에게 문의하세요.
        """)

if __name__ == "__main__":
    main() 