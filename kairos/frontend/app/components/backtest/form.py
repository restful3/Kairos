"""
백테스트 설정 폼 컴포넌트 모듈입니다.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import logging

from ...services.backtest_api import BacktestAPI

logger = logging.getLogger(__name__)

def render_backtest_form(strategy, on_submit=None):
    """
    백테스팅 폼을 렌더링합니다.
    
    Args:
        strategy: 전략 정보
        on_submit: 폼 제출 시 실행될 콜백 함수
    """
    st.subheader("📊 백테스팅 설정")
    
    with st.form("backtest_form"):
        # 전략 정보
        strategy_id = strategy["id"]
        strategy_name = strategy["name"]
        stock_code = strategy.get("stock_code", "")
        stock_name = strategy.get("stock_name", "")
        
        st.write(f"**전략**: {strategy_name}")
        st.write(f"**종목**: {stock_name} ({stock_code})")
        
        # 구분선
        st.divider()
        
        # 백테스팅 파라미터 설정
        col1, col2 = st.columns(2)
        
        with col1:
            # 기간 선택
            period_options = {
                "90": "최근 3개월",
                "180": "최근 6개월",
                "365": "최근 1년",
                "730": "최근 2년",
                "1095": "최근 3년",
                "1825": "최근 5년"
            }
            selected_period = st.selectbox(
                "백테스팅 기간",
                options=list(period_options.keys()),
                format_func=lambda x: period_options[x],
                index=0
            )
            days = int(selected_period)
            
            # 초기 자본금
            initial_capital = st.number_input(
                "초기 자본금",
                min_value=1000000,
                max_value=1000000000,
                value=10000000,
                step=1000000,
                format="%d"
            )
            
        with col2:
            # 거래 수수료
            fee_rate = st.number_input(
                "거래 수수료 (%)",
                min_value=0.0,
                max_value=1.0,
                value=0.015,
                step=0.001,
                format="%.3f"
            ) / 100  # 백분율을 소수로 변환
            
            # 실제 데이터 사용 여부
            use_real_data = st.checkbox("실제 거래 데이터 사용", value=True)
        
        # 구분선
        st.divider()
        
        # 제출 버튼
        submit_button = st.form_submit_button("백테스팅 실행")
        
    # 폼 제출 시
    if submit_button:
        with st.spinner("백테스팅을 실행 중입니다..."):
            try:
                backtest_api = BacktestAPI()
                result = backtest_api.run_backtest(
                    strategy_id=strategy_id,
                    days=days,
                    initial_capital=initial_capital,
                    fee_rate=fee_rate,
                    use_real_data=use_real_data
                )
                
                # 에러 체크
                if "error" in result:
                    st.error(f"백테스팅 실행 중 오류가 발생했습니다: {result['error']}")
                    return None
                
                # 백테스팅 정보 저장
                st.session_state.backtest_result = result
                st.session_state.backtest_params = {
                    "strategy_id": strategy_id,
                    "days": days,
                    "initial_capital": initial_capital,
                    "fee_rate": fee_rate,
                    "use_real_data": use_real_data,
                    "period": period_options[selected_period]
                }
                
                # 성공 메시지
                st.success("백테스팅이 성공적으로 완료되었습니다!")
                
                # 콜백 실행
                if on_submit:
                    on_submit(result)
                    
                return result
                
            except Exception as e:
                logger.error(f"백테스팅 실행 중 오류 발생: {str(e)}")
                st.error(f"백테스팅 실행 중 오류가 발생했습니다: {str(e)}")
                return None
    
    return None 