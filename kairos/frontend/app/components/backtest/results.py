"""
백테스트 결과 표시 컴포넌트 모듈입니다.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
from plotly.subplots import make_subplots
from typing import Dict, List, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def render_backtest_result(backtest_result: Dict[str, Any]):
    """
    백테스팅 결과를 표시합니다.
    
    Args:
        backtest_result: 백테스트 결과 데이터
    """
    st.markdown('<div class="section-header">백테스팅 결과</div>', unsafe_allow_html=True)
    
    strategy = backtest_result.get('strategy', {})
    metrics = backtest_result.get('metrics', {})
    trades = backtest_result.get('trades', [])
    portfolio_values = backtest_result.get('portfolio_values', [])
    
    # 요약 결과 카드
    with st.container():
        st.markdown(f"### '{strategy.get('name', '알 수 없음')}' 백테스팅 결과")
        
        # 시작일 / 종료일
        if portfolio_values:
            start_date = portfolio_values[0]['date'].strftime("%Y-%m-%d")
            end_date = portfolio_values[-1]['date'].strftime("%Y-%m-%d")
            st.markdown(f"**백테스팅 기간:** {start_date} ~ {end_date}")
        
        # 데이터 소스 표시
        data_source = backtest_result.get("backtest_params", {}).get("use_real_data", False)
        if data_source:
            st.markdown(f"**데이터 소스:** <span style='color:green;'>실제 시장 데이터</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"**데이터 소스:** <span style='color:orange;'>시뮬레이션 데이터</span>", unsafe_allow_html=True)
        
        # 주요 지표 요약
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_return = metrics.get('total_return', 0)
            return_color = "positive" if total_return > 0 else "negative"
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">총 수익률</div>
                <div class="metric-value {return_color}">{total_return}%</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col2:
            win_rate = metrics.get('win_rate', 0)
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">승률</div>
                <div class="metric-value">{win_rate}%</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col3:
            max_drawdown = metrics.get('max_drawdown', 0)
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">최대 낙폭</div>
                <div class="metric-value negative">{max_drawdown}%</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col4:
            sharpe_ratio = metrics.get('sharpe_ratio', 0)
            sharpe_color = "positive" if sharpe_ratio > 1 else "negative"
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">샤프 지수</div>
                <div class="metric-value {sharpe_color}">{sharpe_ratio}</div>
            </div>
            ''', unsafe_allow_html=True)
        
        # 추가 지표
        col1, col2 = st.columns(2)
        
        with col1:
            annualized_return = metrics.get('annualized_return', 0)
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">연간화 수익률</div>
                <div class="metric-value {'positive' if annualized_return > 0 else 'negative'}">{annualized_return}%</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col2:
            volatility = metrics.get('volatility', 0)
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">변동성 (연간화)</div>
                <div class="metric-value">{volatility}%</div>
            </div>
            ''', unsafe_allow_html=True)
    
    # 포트폴리오 가치 추이 차트
    if portfolio_values:
        with st.container():
            st.markdown("### 백테스팅 차트")
            
            # 데이터 준비
            df = pd.DataFrame(portfolio_values)
            
            # 일자별 포트폴리오 가치 차트
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                row_heights=[0.7, 0.3],
                                subplot_titles=('포트폴리오 가치 추이', '일간 수익률'),
                                vertical_spacing=0.1)
            
            # 포트폴리오 가치 추이
            fig.add_trace(
                go.Scatter(
                    x=df['date'], 
                    y=df['total_value'],
                    mode='lines',
                    name='포트폴리오 가치',
                    line=dict(color='blue', width=2)
                ),
                row=1, col=1
            )
            
            # 매수/매도 표시
            if trades:
                buy_dates = [t['date'] for t in trades if t['type'] == 'buy']
                buy_values = [portfolio_values[next(i for i, v in enumerate(portfolio_values) if v['date'] == d)]['total_value'] for d in buy_dates]
                
                sell_dates = [t['date'] for t in trades if t['type'] == 'sell']
                sell_values = [portfolio_values[next(i for i, v in enumerate(portfolio_values) if v['date'] == d)]['total_value'] for d in sell_dates]
                
                fig.add_trace(
                    go.Scatter(
                        x=buy_dates,
                        y=buy_values,
                        mode='markers',
                        name='매수',
                        marker=dict(color='green', size=10, symbol='triangle-up')
                    ),
                    row=1, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=sell_dates,
                        y=sell_values,
                        mode='markers',
                        name='매도',
                        marker=dict(color='red', size=10, symbol='triangle-down')
                    ),
                    row=1, col=1
                )
            
            # 일간 수익률
            df['daily_return'] = df['total_value'].pct_change() * 100
            fig.add_trace(
                go.Bar(
                    x=df['date'],
                    y=df['daily_return'],
                    name='일간 수익률',
                    marker_color=['red' if r < 0 else 'green' for r in df['daily_return']]
                ),
                row=2, col=1
            )
            
            # 차트 레이아웃 설정
            fig.update_layout(
                height=600,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=0, r=0, t=30, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # 거래 기록
    if trades:
        with st.container():
            st.markdown("### 거래 내역")
            
            # 거래 데이터 변환
            trade_df = pd.DataFrame(trades)
            
            # 타입에 따라 한글 표시
            trade_df['타입'] = trade_df['type'].map({'buy': '매수', 'sell': '매도'})
            
            # 필요한 열만 선택하고 이름 변경
            display_df = trade_df[[
                'date', '타입', 'price', 'quantity', 'amount', 'reason'
            ]].rename(columns={
                'date': '일자',
                'price': '가격',
                'quantity': '수량',
                'amount': '거래대금',
                'reason': '사유'
            })
            
            # 소수점 반올림
            display_df['가격'] = display_df['가격'].round(2)
            display_df['거래대금'] = display_df['거래대금'].round(0).astype(int)
            
            # 테이블로 표시
            st.dataframe(display_df, hide_index=True)
    
    # 백테스팅 결과 저장 버튼
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("백테스팅 결과 저장", use_container_width=True):
            # 여기에 저장 로직 추가
            st.success("백테스팅 결과가 저장되었습니다.")
    
    with col2:
        if st.button("새 백테스트 실행", use_container_width=True):
            # 결과 초기화 및 폼으로 이동
            st.session_state.backtest_result = None
            st.rerun()

def render_backtest_results(backtest_results, strategy=None):
    """
    백테스트 결과를 표시합니다.
    
    Args:
        backtest_results: 백테스트 결과 데이터
        strategy: 전략 정보 (기본값: None)
    """
    if not backtest_results:
        st.info("백테스트 결과가 없습니다.")
        return
    
    # 문자열인 경우 처리
    if isinstance(backtest_results, str):
        try:
            # JSON 문자열을 파싱해봅니다
            backtest_results = json.loads(backtest_results)
        except:
            # 파싱이 안 되면 그냥 문자열로 표시
            st.info(f"백테스트 결과: {backtest_results}")
            return
    
    # 결과가 리스트인 경우 (백테스트 히스토리)
    if isinstance(backtest_results, list):
        if not backtest_results:
            st.info("백테스트 히스토리가 없습니다.")
            return
            
        # 모든 항목이 문자열인지 확인
        all_strings = all(isinstance(item, str) for item in backtest_results)
        if all_strings:
            st.info("백테스트 히스토리가 처리할 수 없는 형식입니다.")
            st.write(backtest_results)
            return
            
        # 가장 최근 백테스트 결과 표시
        latest_result = backtest_results[-1]
        if isinstance(latest_result, str):
            try:
                latest_result = json.loads(latest_result)
            except:
                st.info(f"최근 백테스트 결과: {latest_result}")
                return
        
        # 결과 요약 탭
        st.subheader("📊 최근 백테스트 결과")
        
        # 메트릭스 표시
        _display_metrics(latest_result)
        
        # 백테스트 히스토리 표시
        st.subheader("📝 백테스트 히스토리")
        
        # 데이터프레임으로 변환
        history_df = _create_history_df(backtest_results)
        st.dataframe(history_df)
        
    # 결과가 딕셔너리인 경우 (단일 백테스트 결과)
    else:
        st.subheader("📊 백테스트 결과")
        
        # 메트릭스 표시
        _display_metrics(backtest_results)
        
        # 포트폴리오 성과 차트
        if "portfolio_values" in backtest_results:
            _plot_portfolio_performance(backtest_results["portfolio_values"])
        
        # 매매 내역
        if "trades" in backtest_results:
            _display_trades(backtest_results["trades"])

def _display_metrics(backtest_result):
    """백테스트 메트릭스를 표시합니다."""
    if not backtest_result:
        return
    
    # 문자열인 경우 처리
    if isinstance(backtest_result, str):
        try:
            backtest_result = json.loads(backtest_result)
        except:
            st.info(f"메트릭스 정보: {backtest_result}")
            return
        
    metrics = backtest_result.get("metrics", {})
    if not metrics and isinstance(backtest_result, dict):
        # metrics 키가 없는 경우 직접 메트릭스 정보를 찾아봅니다
        metrics = {
            "total_return": backtest_result.get("return", 0),
            "win_rate": backtest_result.get("win_rate", 0),
            "max_drawdown": backtest_result.get("max_drawdown", 0)
        }
    
    if not metrics:
        st.info("백테스트 메트릭스 정보가 없습니다.")
        return
    
    # 메트릭스 컬럼
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_return = metrics.get("total_return", 0)
        st.metric("총 수익률", f"{total_return:.2f}%", delta=None)
        
        win_rate = metrics.get("win_rate", 0)
        st.metric("승률", f"{win_rate:.2f}%", delta=None)
    
    with col2:
        annualized_return = metrics.get("annualized_return", 0)
        st.metric("연간 수익률", f"{annualized_return:.2f}%", delta=None)
        
        max_drawdown = metrics.get("max_drawdown", 0)
        st.metric("최대 낙폭", f"{max_drawdown:.2f}%", delta=None)
    
    with col3:
        volatility = metrics.get("volatility", 0)
        st.metric("변동성", f"{volatility:.2f}%", delta=None)
        
        total_trades = metrics.get("total_trades", 0)
        st.metric("거래 횟수", f"{total_trades}회", delta=None)
    
    with col4:
        sharpe_ratio = metrics.get("sharpe_ratio", 0)
        st.metric("샤프 비율", f"{sharpe_ratio:.2f}", delta=None)
        
        # 백테스트 파라미터
        params = backtest_result.get("backtest_params", backtest_result.get("params", {}))
        days = params.get("days", 0)
        st.metric("백테스팅 기간", f"{days}일", delta=None)

def _create_history_df(backtest_history):
    """백테스트 히스토리를 데이터프레임으로 변환합니다."""
    history_data = []
    
    for result in backtest_history:
        if not result:
            continue
            
        # 문자열인 경우 처리
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except:
                # 파싱이 안 되면 건너뜁니다
                continue
                
        # 날짜 정보
        date = result.get("date", "")
        if isinstance(date, str):
            if "T" in date:
                date = date.split("T")[0]
            elif " " in date:
                date = date.split(" ")[0]
                
        # 메트릭스 정보
        metrics = result.get("metrics", {})
        if not metrics and isinstance(result, dict):
            # metrics 키가 없는 경우 직접 메트릭스 정보를 찾아봅니다
            metrics = {
                "total_return": result.get("return", 0),
                "win_rate": result.get("win_rate", 0),
                "max_drawdown": result.get("max_drawdown", 0)
            }
        
        # 파라미터 정보
        params = result.get("params", result.get("backtest_params", {}))
        
        # 정리된 정보
        history_data.append({
            "날짜": date,
            "총 수익률(%)": metrics.get("total_return", result.get("return", 0)),
            "승률(%)": metrics.get("win_rate", result.get("win_rate", 0)),
            "최대낙폭(%)": metrics.get("max_drawdown", result.get("max_drawdown", 0)),
            "기간(일)": params.get("days", 0),
            "실제 데이터": params.get("use_real_data", result.get("use_real_data", False))
        })
    
    # 데이터프레임 생성 및 정렬
    df = pd.DataFrame(history_data)
    if not df.empty:
        df = df.sort_values(by="날짜", ascending=False)
    
    return df

def _plot_portfolio_performance(portfolio_values):
    """포트폴리오 성과 차트를 그립니다."""
    if not portfolio_values:
        return
    
    # 데이터 준비
    df = pd.DataFrame(portfolio_values)
    
    # 일자별 포트폴리오 가치 차트
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        row_heights=[0.7, 0.3],
                        subplot_titles=('포트폴리오 가치 추이', '일간 수익률'),
                        vertical_spacing=0.1)
    
    # 포트폴리오 가치 추이
    fig.add_trace(
        go.Scatter(
            x=df['date'], 
            y=df['total_value'],
            mode='lines',
            name='포트폴리오 가치',
            line=dict(color='blue', width=2)
        ),
        row=1, col=1
    )
    
    # 일간 수익률
    df['daily_return'] = df['total_value'].pct_change() * 100
    fig.add_trace(
        go.Bar(
            x=df['date'],
            y=df['daily_return'],
            name='일간 수익률',
            marker_color=['red' if r < 0 else 'green' for r in df['daily_return']]
        ),
        row=2, col=1
    )
    
    # 차트 레이아웃 설정
    fig.update_layout(
        height=600,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def _display_trades(trades):
    """거래 내역을 표시합니다."""
    if not trades:
        return
    
    # 거래 데이터 변환
    trade_df = pd.DataFrame(trades)
    
    # 타입에 따라 한글 표시
    trade_df['타입'] = trade_df['type'].map({'buy': '매수', 'sell': '매도'})
    
    # 필요한 열만 선택하고 이름 변경
    display_df = trade_df[[
        'date', '타입', 'price', 'quantity', 'amount', 'reason'
    ]].rename(columns={
        'date': '일자',
        'price': '가격',
        'quantity': '수량',
        'amount': '거래대금',
        'reason': '사유'
    })
    
    # 소수점 반올림
    display_df['가격'] = display_df['가격'].round(2)
    display_df['거래대금'] = display_df['거래대금'].round(0).astype(int)
    
    # 테이블로 표시
    st.dataframe(display_df, hide_index=True) 