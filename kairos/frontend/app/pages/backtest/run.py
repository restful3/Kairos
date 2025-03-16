import streamlit as st
import pandas as pd
from datetime import datetime
import logging

from ...components.backtest.form import render_backtest_form
from ...components.backtest.results import render_backtest_results
from ...services.strategy_service import StrategyService

logger = logging.getLogger(__name__)

def render():
    """백테스트 실행 페이지"""
    st.title("🧪 백테스팅")
    
    # 이전 페이지로 이동 버튼
    col1, col2 = st.columns([2, 10])
    with col1:
        if st.button("← 뒤로", use_container_width=True):
            # 이전 상태로 돌아가기
            if "backtest_strategy" in st.session_state:
                st.session_state.current_strategy = st.session_state.backtest_strategy
                st.session_state.strategy_view_mode = "detail"
                st.session_state.current_page = "strategy"
            else:
                st.session_state.strategy_view_mode = "list"
                st.session_state.current_page = "strategy"
            
            # 페이지 새로고침
            st.rerun()
    
    # 전략 확인
    if "backtest_strategy" not in st.session_state:
        st.error("백테스팅할 전략이 선택되지 않았습니다. 전략 목록에서 전략을 선택해주세요.")
        
        # 전략 목록 페이지로 이동 버튼
        if st.button("전략 목록으로 이동"):
            st.session_state.strategy_view_mode = "list"
            st.session_state.current_page = "strategy"
            st.rerun()
            
        return
    
    # 현재 선택된 전략
    strategy = st.session_state.backtest_strategy
    
    # 시각적 구분선
    st.markdown("---")
    
    # 백테스트 폼과 결과를 탭으로 표시
    tab1, tab2 = st.tabs(["백테스트 설정", "백테스트 결과"])
    
    with tab1:
        # 백테스트 폼 렌더링
        def on_backtest_submit(result):
            # 폼이 제출되면 결과 탭으로 전환
            st.session_state.active_tab = "results"
            # 전역 상태에 백테스트 결과 저장
            st.session_state.backtest_current_result = result
            # 탭 전환
            tab2.active = True
        
        # 백테스트 폼 렌더링
        result = render_backtest_form(strategy, on_submit=on_backtest_submit)
        
        # 백테스트 히스토리 표시
        if "backtest_history" in strategy and strategy["backtest_history"]:
            st.subheader("📜 백테스트 히스토리")
            render_backtest_results(strategy["backtest_history"])
    
    with tab2:
        # 현재 백테스트 결과
        if "backtest_current_result" in st.session_state:
            render_backtest_results(st.session_state.backtest_current_result)
        elif "backtest_result" in st.session_state:
            render_backtest_results(st.session_state.backtest_result)
        else:
            st.info("백테스트를 실행하세요.")
            
            # 가장 최근 백테스트 히스토리 표시 (있는 경우)
            if "backtest_history" in strategy and strategy["backtest_history"]:
                st.subheader("📜 최근 백테스트 결과")
                render_backtest_results(strategy["backtest_history"][-1]) 