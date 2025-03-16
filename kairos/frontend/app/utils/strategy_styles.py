import streamlit as st
from app.utils.styles import load_common_styles

def load_strategy_styles():
    """전략 생성 페이지용 CSS 스타일을 로드합니다"""
    # 공통 스타일 로드
    load_common_styles()
    
    # 페이지 전용 추가 스타일
    st.markdown("""
    <style>
    .strategy-card {
        background-color: #f0f7ff;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        border-left: 4px solid #1d3557;
        height: 100%;
        position: relative;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .strategy-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    .strategy-card h3 {
        margin-top: 0;
        margin-bottom: 10px;
        font-size: 1.2rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .strategy-info {
        margin-bottom: 10px;
    }
    
    .strategy-status {
        font-size: 0.9rem;
        padding: 3px 8px;
        border-radius: 10px;
        background-color: #f0f0f0;
        display: inline-block;
        margin-top: 8px;
    }
    
    .strategy-status.active {
        background-color: #d1ffd1;
        color: #008800;
    }
    
    .strategy-status.inactive {
        background-color: #f0f0f0;
        color: #666;
    }
    
    .backtest-summary {
        margin-top: 10px;
        font-size: 0.9rem;
        padding: 5px;
        background-color: #f8f8f8;
        border-radius: 5px;
    }
    
    .backtest-result {
        font-weight: bold;
    }
    
    .backtest-result.positive {
        color: #e63946;
    }
    
    .backtest-result.negative {
        color: #1d3557;
    }
    
    .parameter-section {
        background-color: #fcfcfc;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    
    .filter-bar {
        background-color: #f9f9f9;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    
    .backtest-modal {
        background-color: #f9f9f9;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
        border: 1px solid #ddd;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True) 