import streamlit as st
import pandas as pd
from typing import Dict, Any

def show_account_summary(account_balance: Dict[str, Any]):
    """계좌 요약 정보 표시"""
    deposit = account_balance.get("deposit", 0)
    total_evaluated_price = account_balance.get("total_evaluated_price", 0)
    total_purchase_price = account_balance.get("total_purchase_price", 0)
    
    # 총 자산, 총 손익, 총 손익률 계산
    total_asset = deposit + total_evaluated_price
    total_profit_loss = total_evaluated_price - total_purchase_price
    total_profit_loss_rate = (total_profit_loss / total_purchase_price * 100) if total_purchase_price > 0 else 0
    
    # 계좌 요약 정보 표시
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="총 자산",
            value=f"{total_asset:,}원",
            help="예수금 + 주식평가금액"
        )
    
    with col2:
        st.metric(
            label="예수금",
            value=f"{deposit:,}원",
            help="주문 가능한 현금"
        )
    
    with col3:
        st.metric(
            label="주식평가금액",
            value=f"{total_evaluated_price:,}원",
            delta=f"{total_profit_loss:,}원 ({total_profit_loss_rate:.2f}%)",
            delta_color="normal" if total_profit_loss >= 0 else "inverse",
            help="보유주식 평가금액 (평가손익)"
        )

def show_stock_list(stocks: list):
    """보유 종목 목록 표시"""
    if not stocks or len(stocks) == 0:
        st.info("보유 종목이 없습니다.")
        return
    
    # 데이터프레임 생성
    df = pd.DataFrame(stocks)
    
    # 열 이름 변경
    df = df.rename(columns={
        "symbol": "종목코드", 
        "name": "종목명", 
        "quantity": "보유수량", 
        "avg_price": "매입단가", 
        "current_price": "현재가",
        "profit_loss_rate": "손익률(%)",
        "profit_loss": "손익금액",
        "sellable_quantity": "매도가능수량"
    })
    
    # 열 순서 조정
    df = df[["종목코드", "종목명", "보유수량", "매입단가", "현재가", "손익률(%)", "손익금액", "매도가능수량"]]
    
    # 숫자 형식 조정
    df["매입단가"] = df["매입단가"].map(lambda x: f"{x:,.0f}")
    df["현재가"] = df["현재가"].map(lambda x: f"{x:,.0f}")
    df["손익률(%)"] = df["손익률(%)"].map(lambda x: f"{x:.2f}")
    df["손익금액"] = df["손익금액"].map(lambda x: f"{x:,.0f}")
    
    # 테이블 표시
    st.dataframe(df, use_container_width=True) 