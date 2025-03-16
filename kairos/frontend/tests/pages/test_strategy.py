import streamlit as st
import pandas as pd
from datetime import datetime

def show():
    """테스트용 간소화된 전략 생성 페이지"""
    st.title("테스트 - 간소화된 전략 생성")
    
    # 기본 정보 입력
    strategy_name = st.text_input("전략 이름", value="테스트 전략")
    
    # 종목 정보 직접 입력
    st.subheader("종목 정보 직접 입력")
    
    col1, col2 = st.columns(2)
    with col1:
        stock_code = st.text_input("종목코드", value="005930")
    with col2:
        stock_name = st.text_input("종목명", value="삼성전자")
    
    # 전략 유형 선택
    strategy_type = st.selectbox(
        "전략 유형",
        ["이동평균선 교차 전략", "RSI 과매수/과매도 전략", "가격 돌파 전략"]
    )
    
    # 간단한 전략 파라미터
    st.subheader("전략 파라미터")
    
    if strategy_type == "이동평균선 교차 전략":
        short_period = st.slider("단기 이동평균 기간", 5, 30, 5)
        long_period = st.slider("장기 이동평균 기간", 20, 120, 20)
        strategy_params = {
            "short_period": short_period,
            "long_period": long_period
        }
    elif strategy_type == "RSI 과매수/과매도 전략":
        rsi_period = st.slider("RSI 계산 기간", 5, 30, 14)
        oversold = st.slider("과매도 기준", 10, 40, 30)
        overbought = st.slider("과매수 기준", 60, 90, 70)
        strategy_params = {
            "rsi_period": rsi_period,
            "oversold": oversold,
            "overbought": overbought
        }
    else:  # 가격 돌파 전략
        target_price = st.number_input("기준 가격(원)", min_value=0, value=50000, step=1000)
        direction = st.radio("돌파 방향", ["상향 돌파", "하향 돌파"])
        strategy_params = {
            "target_price": target_price,
            "direction": direction
        }
    
    # 매도 조건 설정
    st.subheader("매도 조건")
    take_profit = st.slider("목표 수익률(%)", 1.0, 30.0, 5.0, 0.5)
    stop_loss = st.slider("손절 손실률(%)", -30.0, -1.0, -5.0, 0.5)
    
    # 투자 설정
    st.subheader("투자 설정")
    investment_amount = st.number_input("1회 투자금액(원)", min_value=10000, max_value=10000000, value=100000, step=10000)
    
    # 저장 버튼 - 조건 없이 항상 표시
    save_button = st.button("전략 저장", use_container_width=True)
    
    if save_button:
        if not stock_code or not stock_name:
            st.error("전략을 저장하기 전에 반드시 종목을 선택해주세요.")
            return
        
        # 새 전략 객체 생성
        new_strategy = {
            "name": strategy_name,
            "stock_code": stock_code,
            "stock_name": stock_name,
            "strategy_type": strategy_type,
            "params": strategy_params,
            "take_profit": take_profit,
            "stop_loss": stop_loss,
            "investment_amount": investment_amount,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        # 세션 상태에 저장
        if "saved_strategies" not in st.session_state:
            st.session_state.saved_strategies = []
        
        st.session_state.saved_strategies.append(new_strategy)
        
        # 저장 완료 메시지
        st.success(f"전략 '{strategy_name}'이(가) 저장되었습니다.")
        
        # 저장된 전략 정보 표시
        st.json(new_strategy)

if __name__ == "__main__":
    show() 