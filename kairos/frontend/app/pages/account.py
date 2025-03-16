import streamlit as st
import pandas as pd
import os
from datetime import datetime

from app.api.client import api_client
from app.utils.session import set_account_balance, get_account_balance
from app.components.account import show_account_summary, show_stock_list
from app.components.charts import portfolio_chart, profit_loss_chart

def show():
    """계좌 정보 페이지 표시"""
    
    st.title("계좌 정보")
    
    # 계좌 정보 조회 버튼
    if st.button("계좌 정보 새로고침", use_container_width=True):
        with st.spinner("계좌 정보를 조회하고 있습니다..."):
            try:
                # 계좌 정보 조회
                balance_data = api_client.get_account_balance()
                
                # 세션에 계좌 정보 저장
                set_account_balance(balance_data)
                
                st.success("계좌 정보가 갱신되었습니다.")
            except Exception as e:
                st.error(f"계좌 정보 조회 실패: {str(e)}")
    
    # 현재 계좌 정보 표시
    account_balance = get_account_balance()
    
    if not account_balance:
        # 계좌 정보가 없는 경우 조회 시도
        with st.spinner("계좌 정보를 조회하고 있습니다..."):
            try:
                # 계좌 정보 조회
                account_balance = api_client.get_account_balance()
                
                # 세션에 계좌 정보 저장
                set_account_balance(account_balance)
            except Exception as e:
                st.error(f"계좌 정보 조회 실패: {str(e)}")
                return
    
    # 시간 표시
    st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 계좌 요약 정보 표시
    show_account_summary(account_balance)
    
    # 구분선
    st.divider()
    
    # 보유 종목 목록 표시
    st.subheader("보유 종목 목록")
    show_stock_list(account_balance.get("stocks", []))
    
    # 구분선
    st.divider()
    
    # 차트 표시
    st.subheader("포트폴리오 분석")
    
    stocks = account_balance.get("stocks", [])
    if stocks and len(stocks) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = portfolio_chart(stocks)
            if fig1:
                st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = profit_loss_chart(stocks)
            if fig2:
                st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("보유 종목이 없어 차트를 표시할 수 없습니다.")

# __init__.py에서 호출하는 함수 이름과 일치시키기 위한 별칭 함수
def render_account_page():
    """
    계좌 정보 페이지 렌더링 (리팩토링 호환용)
    기존 show 함수를 호출합니다.
    """
    return show() 