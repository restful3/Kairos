import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict, Any

def portfolio_chart(stocks: List[Dict[str, Any]]):
    """포트폴리오 구성 파이 차트"""
    if not stocks or len(stocks) == 0:
        st.info("보유 종목이 없습니다.")
        return
    
    # 데이터 준비
    symbols = []
    values = []
    colors = []
    
    for stock in stocks:
        stock_value = stock["current_price"] * stock["quantity"]
        symbols.append(f"{stock['name']} ({stock['symbol']})")
        values.append(stock_value)
        
        # 수익률에 따른 색상 지정
        if stock["profit_loss_rate"] > 0:
            colors.append("red")
        elif stock["profit_loss_rate"] < 0:
            colors.append("blue")
        else:
            colors.append("gray")
    
    # 파이 차트 생성
    fig = go.Figure(data=[go.Pie(
        labels=symbols,
        values=values,
        hole=.4,
        marker_colors=colors
    )])
    
    fig.update_layout(
        title="포트폴리오 구성",
        height=400
    )
    
    return fig

def profit_loss_chart(stocks: List[Dict[str, Any]]):
    """종목별 손익 바 차트"""
    if not stocks or len(stocks) == 0:
        st.info("보유 종목이 없습니다.")
        return
    
    # 데이터 준비
    symbols = []
    profits = []
    colors = []
    
    for stock in stocks:
        symbols.append(f"{stock['name']} ({stock['symbol']})")
        profits.append(stock["profit_loss"])
        
        # 수익률에 따른 색상 지정
        if stock["profit_loss"] > 0:
            colors.append("red")
        elif stock["profit_loss"] < 0:
            colors.append("blue")
        else:
            colors.append("gray")
    
    # 바 차트 생성
    fig = go.Figure(data=[go.Bar(
        x=symbols,
        y=profits,
        marker_color=colors
    )])
    
    fig.update_layout(
        title="종목별 손익",
        xaxis_title="종목",
        yaxis_title="손익금액(원)",
        height=400
    )
    
    return fig 