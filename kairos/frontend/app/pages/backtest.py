"""
백테스팅 페이지 모듈입니다.
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import logging

from ..api.client import api_client
from ..utils.session import is_logged_in, get_user_info
from ..utils.styles import load_common_styles
from ..utils.backtest_utils import run_backtest_simulation
from ..components.backtest.form import render_backtest_form
from ..components.backtest.results import render_backtest_result
from ..services.stock_service import StockService

# 로깅 설정
logger = logging.getLogger(__name__)

def render_backtest_page():
    """백테스팅 페이지 표시"""
    st.title("📊 백테스팅")
    
    # CSS 스타일 로드
    load_common_styles()
    
    # 로그인 확인
    if not is_logged_in():
        st.warning("백테스팅을 위해서는 로그인이 필요합니다.")
        return
    
    # 뒤로가기 버튼
    if st.session_state.get("previous_page") == "strategy_detail":
        if st.button("← 전략 상세로 돌아가기"):
            st.session_state.current_page = "strategy"
            st.session_state.strategy_view_mode = "detail"
            st.rerun()
    
    # 백테스트 결과가 있으면 표시
    if "backtest_result" in st.session_state and st.session_state.backtest_result:
        render_backtest_result(st.session_state.backtest_result)
        return
    
    # 전략 목록 가져오기
    try:
        strategies = api_client.get_strategies()
        if not strategies:
            st.info("백테스팅을 위한 전략이 없습니다. 전략을 먼저 생성해주세요.")
            
            # 전략 생성 페이지로 이동 버튼
            if st.button("전략 생성 페이지로 이동"):
                st.session_state.current_page = "strategy"
                st.session_state.strategy_view_mode = "create"
                st.rerun()
            
            return
    except Exception as e:
        logger.error(f"전략 목록 로드 실패: {str(e)}")
        st.error("전략 목록을 불러오는데 실패했습니다.")
        return
    
    # 백테스트 폼 렌더링
    render_backtest_form(strategies, on_run=_handle_run_backtest)

def _handle_run_backtest(strategy, params):
    """백테스트 실행 처리"""
    try:
        logger.info(f"백테스트 실행: {strategy.get('name', '알 수 없음')}")
        
        with st.spinner("백테스트를 실행 중입니다..."):
            # 백테스트 실행
            result = run_backtest_simulation(
                strategy=strategy,
                days=params["days"],
                initial_capital=params["initial_capital"],
                fee_rate=params["fee_rate"],
                use_real_data=params["use_real_data"]
            )
            
            if result:
                # 백테스트 결과 저장
                backtest_history = strategy.get("backtest_history", [])
                backtest_history.append({
                    "date": datetime.now().isoformat(),
                    "params": params,
                    "metrics": result["metrics"]
                })
                
                # 백엔드에 업데이트
                strategy["backtest_history"] = backtest_history
                success = api_client.update_strategy(strategy["id"], strategy)
                
                if success:
                    logger.info("백테스트 결과 저장 성공")
                else:
                    logger.warning("백테스트 결과 저장 실패")
                
                # 결과 세션에 저장
                st.session_state.backtest_result = result
                st.rerun()
            else:
                st.error("백테스트 실행에 실패했습니다.")
    except Exception as e:
        logger.error(f"백테스트 실행 실패: {str(e)}")
        st.error(f"백테스트 실행 중 오류가 발생했습니다: {str(e)}")

# 이전 함수 이름과의 호환성을 위한 별칭
show = render_backtest_page

if __name__ == "__main__":
    render_backtest_page()