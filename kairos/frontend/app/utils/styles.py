import streamlit as st

def load_common_styles():
    """공통으로, 사용되는 CSS 스타일을 로드합니다."""
    st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    .section-header {
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        font-weight: bold;
        border-bottom: 1px solid #eee;
        padding-bottom: 0.5rem;
    }
    
    .info-card {
        background-color: #f9f9f9;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .result-card {
        background-color: #f0f7ff;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background-color: #f0f7ff;
        border-radius: 5px;
        padding: 10px;
        margin: 5px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .positive { color: #e63946; }
    .negative { color: #1d3557; }
    </style>
    """, unsafe_allow_html=True) 