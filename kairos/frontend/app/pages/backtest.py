import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
import random

from app.api.client import api_client
from app.utils.session import is_logged_in
from app.utils.styles import load_common_styles
from app.utils.backtest_utils import run_backtest_simulation
from app.pages.strategy_builder import save_strategies, load_strategies

# 기본 CSS 스타일 정의
def load_css():
    """백테스팅 페이지용 CSS 스타일을 로드합니다"""
    # 공통 스타일 로드
    load_common_styles()
    
    # 페이지 전용 추가 스타일
    st.markdown("""
    <style>
    .metric-value {
        font-size: 1.5rem;
        font-weight: bold;
    }
    
    .metric-label {
        font-size: 0.8rem;
        color: #666;
    }
    
    .backtest-settings {
        background-color: #fcfcfc;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 3px solid #4CAF50;
    }
    
    .trade-table {
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)


def show():
    """백테스팅 페이지 표시"""
    st.title("백테스팅")
    
    # CSS 스타일 로드
    load_css()
    
    # 사용자가 로그인했는지 확인
    if not is_logged_in():
        st.error("백테스팅을 실행하려면 먼저 로그인이 필요합니다.")
        return
    
    # 저장된 전략 목록 불러오기
    if "saved_strategies" not in st.session_state:
        user_id = st.session_state.get("user_id", "default")
        st.session_state.saved_strategies = load_strategies(user_id)
    
    strategies = st.session_state.saved_strategies
    
    if not strategies:
        st.warning("백테스팅을 실행할 전략이 없습니다. 전략 생성 페이지에서 먼저 전략을 만들어 주세요.")
        return
    
    # 전략 선택 및 백테스팅 설정
    st.subheader("백테스팅 설정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 전략이 이미 선택되어 있는지 확인
        if hasattr(st.session_state, 'backtest_strategy'):
            selected_strategy = st.session_state.backtest_strategy
            # 선택된 전략을 목록에서 찾기
            strategy_names = [f"{s['name']} ({s['stock_name']})" for s in strategies]
            default_idx = next((i for i, s in enumerate(strategies) 
                               if s['name'] == selected_strategy['name'] 
                               and s['stock_code'] == selected_strategy['stock_code']), 0)
        else:
            strategy_names = [f"{s['name']} ({s['stock_name']})" for s in strategies]
            default_idx = 0
        
        # 전략 선택
        selected_strategy_name = st.selectbox(
            "백테스팅할 전략 선택",
            options=strategy_names,
            index=default_idx,
            key="backtest_strategy_select"
        )
        
        # 선택된 전략 가져오기
        selected_idx = strategy_names.index(selected_strategy_name)
        selected_strategy = strategies[selected_idx]
        
        # 전략 정보 표시
        st.session_state.backtest_strategy = selected_strategy
        
        # 기간 선택
        period_options_map = {
            "최근 3개월": 90,
            "최근 6개월": 180,
            "최근 1년": 365,
            "최근 3년": 1095,
            "최근 5년": 1825
        }
        
        # 기존 설정값이 있는지 확인
        if hasattr(st.session_state, 'backtest_params') and 'period' in st.session_state.backtest_params:
            default_period = st.session_state.backtest_params['period']
        else:
            default_period = "최근 3개월"
        
        # 기간 선택
        period = st.selectbox(
            "백테스팅 기간",
            options=list(period_options_map.keys()),
            index=list(period_options_map.keys()).index(default_period),
            key="backtest_period"
        )
        
        # 데이터 소스 선택
        use_real_data = st.checkbox(
            "실제 시장 데이터 사용",
            value=st.session_state.get("use_real_data", True),
            help="체크 시 실제 시장 데이터를 사용하고, 해제 시 시뮬레이션 데이터를 사용합니다.",
            key="use_real_data_checkbox"
        )
        st.session_state.use_real_data = use_real_data
        
        if not use_real_data:
            st.info("시뮬레이션 데이터는 실제 시장 상황을 정확히 반영하지 않을 수 있습니다.")
    
    with col2:
        # 초기 자본금 설정
        if hasattr(st.session_state, 'backtest_params') and 'initial_capital' in st.session_state.backtest_params:
            default_capital = st.session_state.backtest_params['initial_capital']
        else:
            default_capital = 10000000
        
        initial_capital = st.number_input(
            "초기 자본금",
            min_value=1000000,
            max_value=1000000000,
            value=int(default_capital),
            step=1000000,
            format="%d",
            key="backtest_capital"
        )
        
        # 수수료율 설정
        if hasattr(st.session_state, 'backtest_params') and 'fee_rate' in st.session_state.backtest_params:
            default_fee = st.session_state.backtest_params['fee_rate'] * 100
        else:
            default_fee = 0.15
        
        fee_rate = st.slider(
            "거래 수수료 (%)",
            min_value=0.0,
            max_value=0.5,
            value=float(default_fee),
            step=0.01,
            key="backtest_fee"
        ) / 100  # 백분율을 소수로 변환
    
    # 백테스팅 실행 버튼
    if st.button("백테스팅 실행", use_container_width=True, key="run_backtest_btn"):
        # 설정 저장
        st.session_state.backtest_params = {
            "period": period,
            "initial_capital": initial_capital,
            "fee_rate": fee_rate
        }
        
        with st.spinner("백테스팅을 실행 중입니다..."):
            try:
                from app.utils.backtest_utils import run_backtest_simulation
                
                # 선택된 기간에 따른 일수 계산
                days = period_options_map[period]
                
                # 백테스팅 실행
                backtest_result = run_backtest_simulation(
                    strategy=selected_strategy,
                    days=days,
                    initial_capital=initial_capital,
                    fee_rate=fee_rate,
                    simplified=False,
                    use_real_data=use_real_data
                )
                
                if backtest_result:
                    st.session_state.backtest_result = backtest_result
                    
                    # 전략 백테스트 이력 업데이트
                    if "backtest_history" not in selected_strategy:
                        selected_strategy["backtest_history"] = []
                    
                    # 백테스트 이력에 결과 추가
                    selected_strategy["backtest_history"].append({
                        "date": backtest_result["date"],
                        "return": backtest_result["metrics"]["total_return"],
                        "win_rate": backtest_result["metrics"]["win_rate"],
                        "max_drawdown": backtest_result["metrics"]["max_drawdown"],
                        "simplified": False,
                        "days": days,
                        "use_real_data": use_real_data
                    })
                    
                    # 업데이트된 전략 저장
                    user_id = st.session_state.get("user_id", "default")
                    save_strategies(user_id)
                    
                    st.success("백테스팅이 완료되었습니다.")
                else:
                    st.error("백테스팅 실행 중 오류가 발생했습니다.")
            except Exception as e:
                st.error(f"백테스팅 실행 중 오류가 발생했습니다: {str(e)}")
    
    # 백테스팅 결과 표시
    if hasattr(st.session_state, 'backtest_result') and st.session_state.backtest_result:
        display_backtest_results(st.session_state.backtest_result)


def display_backtest_results(backtest_result):
    """백테스팅 결과 표시"""
    st.markdown('<div class="section-header">백테스팅 결과</div>', unsafe_allow_html=True)
    
    strategy = backtest_result['strategy']
    metrics = backtest_result['metrics']
    trades = backtest_result['trades']
    portfolio_values = backtest_result['portfolio_values']
    
    # 요약 결과 카드
    with st.container():
        st.markdown(f"### '{strategy['name']}' 백테스팅 결과")
        
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
            return_color = "positive" if metrics['total_return'] > 0 else "negative"
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">총 수익률</div>
                <div class="metric-value {return_color}">{metrics['total_return']}%</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">승률</div>
                <div class="metric-value">{metrics['win_rate']}%</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col3:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">최대 낙폭</div>
                <div class="metric-value negative">{metrics['max_drawdown']}%</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col4:
            sharpe_color = "positive" if metrics['sharpe_ratio'] > 1 else "negative"
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">샤프 지수</div>
                <div class="metric-value {sharpe_color}">{metrics['sharpe_ratio']}</div>
            </div>
            ''', unsafe_allow_html=True)
        
        # 추가 지표
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">연간화 수익률</div>
                <div class="metric-value {'positive' if metrics['annualized_return'] > 0 else 'negative'}">{metrics['annualized_return']}%</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">변동성 (연간화)</div>
                <div class="metric-value">{metrics['volatility']}%</div>
            </div>
            ''', unsafe_allow_html=True)
    
    # 포트폴리오 가치 추이 차트
    with st.container():
        st.markdown("### 백테스팅 차트")
        
        if portfolio_values:
            portfolio_df = pd.DataFrame(portfolio_values)
            
            # 주가 및 포트폴리오 가치 차트
            fig = make_subplots(
                rows=2, 
                cols=1, 
                shared_xaxes=True, 
                vertical_spacing=0.03, 
                subplot_titles=("주가 및 포트폴리오 가치", "포지션 크기"),
                row_heights=[0.7, 0.3]
            )
            
            # 주가 차트
            stock_data = backtest_result['stock_data']
            
            # 전략 유형에 따른 추가 시각화
            if strategy['strategy_type'] == "이동평균선 교차 전략":
                signals = backtest_result['signals']
                
                fig.add_trace(
                    go.Scatter(
                        x=signals['date'], 
                        y=signals['ma_short'], 
                        name=f"{strategy['params']['short_period']}일 이평선",
                        line=dict(width=1, color='blue')
                    ),
                    row=1, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=signals['date'], 
                        y=signals['ma_long'], 
                        name=f"{strategy['params']['long_period']}일 이평선",
                        line=dict(width=1, color='orange')
                    ),
                    row=1, col=1
                )
            
            elif strategy['strategy_type'] == "RSI 과매수/과매도 전략":
                signals = backtest_result['signals']
                
                # RSI 값 차트 (추가 subplot)
                fig = make_subplots(
                    rows=3, 
                    cols=1, 
                    shared_xaxes=True, 
                    vertical_spacing=0.03, 
                    subplot_titles=("주가 및 포트폴리오 가치", "RSI", "포지션 크기"),
                    row_heights=[0.5, 0.2, 0.3]
                )
                
                # RSI 값 추가
                fig.add_trace(
                    go.Scatter(
                        x=signals['date'], 
                        y=signals['rsi'], 
                        name="RSI",
                        line=dict(width=1, color='purple')
                    ),
                    row=2, col=1
                )
                
                # RSI 과매수/과매도 라인 추가
                fig.add_hline(
                    y=strategy['params']['overbought'], 
                    line_width=1, 
                    line_dash="dash", 
                    line_color="red",
                    row=2, col=1,
                    annotation_text="과매수"
                )
                
                fig.add_hline(
                    y=strategy['params']['oversold'], 
                    line_width=1, 
                    line_dash="dash", 
                    line_color="green",
                    row=2, col=1,
                    annotation_text="과매도"
                )
            
            elif strategy['strategy_type'] == "가격 돌파 전략":
                # 기준 가격 라인 추가
                fig.add_hline(
                    y=strategy['params']['target_price'], 
                    line_width=1, 
                    line_dash="dash", 
                    line_color="red",
                    row=1, col=1,
                    annotation_text="기준 가격"
                )
            
            # 주가
            fig.add_trace(
                go.Scatter(
                    x=stock_data['date'], 
                    y=stock_data['close'], 
                    name="종가",
                    line=dict(width=1, color='gray')
                ),
                row=1, col=1
            )
            
            # 매수/매도 포인트 표시
            buy_signals = [t for t in trades if t['type'] == 'buy']
            sell_signals = [t for t in trades if t['type'] == 'sell' or t['type'] == 'sell (청산)']
            
            if buy_signals:
                fig.add_trace(
                    go.Scatter(
                        x=[t['date'] for t in buy_signals],
                        y=[t['price'] for t in buy_signals],
                        mode='markers',
                        marker=dict(color='green', size=8, symbol='triangle-up'),
                        name='매수'
                    ),
                    row=1, col=1
                )
            
            if sell_signals:
                fig.add_trace(
                    go.Scatter(
                        x=[t['date'] for t in sell_signals],
                        y=[t['price'] for t in sell_signals],
                        mode='markers',
                        marker=dict(color='red', size=8, symbol='triangle-down'),
                        name='매도'
                    ),
                    row=1, col=1
                )
            
            # 포트폴리오 가치
            fig.add_trace(
                go.Scatter(
                    x=portfolio_df['date'],
                    y=portfolio_df['total_value'],
                    name='포트폴리오 가치',
                    line=dict(width=2, color='blue'),
                    yaxis="y3"
                ),
                row=1, col=1
            )
            
            # 포지션 크기
            fig.add_trace(
                go.Scatter(
                    x=portfolio_df['date'],
                    y=portfolio_df['position'],
                    name='포지션 크기',
                    fill='tozeroy',
                    line=dict(width=1, color='lightblue')
                ),
                row=3 if strategy['strategy_type'] == "RSI 과매수/과매도 전략" else 2, col=1
            )
            
            # 레이아웃 설정
            fig.update_layout(
                height=600,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=0, r=0, t=50, b=0),
                hovermode="x unified",
                yaxis3=dict(
                    title="포트폴리오 가치",
                    overlaying="y",
                    side="right"
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 포트폴리오 가치와 기준 지수 비교 (벤치마크 대비 성과)
            benchmark_values = np.array([v['close'] for v in stock_data.to_dict('records')])
            benchmark_values = benchmark_values / benchmark_values[0] * backtest_result['backtest_params']['initial_capital']
            
            portfolio_values_arr = np.array([v['total_value'] for v in portfolio_values])
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=portfolio_df['date'],
                y=portfolio_values_arr,
                name='전략 성과',
                line=dict(width=2, color='blue')
            ))
            
            fig.add_trace(go.Scatter(
                x=portfolio_df['date'][:len(benchmark_values)],
                y=benchmark_values,
                name='벤치마크 (Buy & Hold)',
                line=dict(width=2, color='gray', dash='dot')
            ))
            
            fig.update_layout(
                title="전략 성과 vs 벤치마크 비교",
                xaxis_title="날짜",
                yaxis_title="자산 가치",
                height=400,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=0, r=0, t=50, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
    # 거래 내역
    with st.container():
        st.markdown("### 거래 내역")
        
        if trades:
            # 거래 내역 데이터프레임 생성
            trades_df = pd.DataFrame(trades)
            
            # 필요한 컬럼만 선택
            display_cols = ['date', 'type', 'price', 'shares']
            
            # 매수/매도에 따라 다른 컬럼 추가
            if 'cost' in trades_df.columns:
                display_cols.append('cost')
            if 'revenue' in trades_df.columns:
                display_cols.append('revenue')
            if 'fee' in trades_df.columns:
                display_cols.append('fee')
            if 'profit_pct' in trades_df.columns:
                display_cols.append('profit_pct')
            
            # 데이터프레임 표시
            st.dataframe(trades_df[trades_df.columns.intersection(display_cols)], use_container_width=True)
            
            # 거래 통계
            buy_trades = [t for t in trades if t['type'] == 'buy']
            sell_trades = [t for t in trades if t['type'] == 'sell' or t['type'] == 'sell (청산)']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("총 거래 횟수", len(trades))
            
            with col2:
                st.metric("매수 횟수", len(buy_trades))
            
            with col3:
                st.metric("매도 횟수", len(sell_trades))
        else:
            st.info("해당 기간 동안 거래 내역이 없습니다.")

if __name__ == "__main__":
    show()