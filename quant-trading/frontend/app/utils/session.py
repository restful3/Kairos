import streamlit as st
from typing import Dict, Any, Optional

def init_session_state():
    """세션 상태 초기화"""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if "token" not in st.session_state:
        st.session_state.token = None
    
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    
    if "account_balance" not in st.session_state:
        st.session_state.account_balance = None

def set_logged_in(value: bool):
    """로그인 상태 설정"""
    st.session_state.logged_in = value

def is_logged_in() -> bool:
    """로그인 상태 확인"""
    return st.session_state.logged_in

def set_token(token: str):
    """토큰 설정"""
    st.session_state.token = token

def get_token() -> Optional[str]:
    """토큰 반환"""
    return st.session_state.token

def set_user_info(user_info: Dict[str, Any]):
    """사용자 정보 설정"""
    st.session_state.user_info = user_info

def get_user_info() -> Optional[Dict[str, Any]]:
    """사용자 정보 반환"""
    return st.session_state.user_info

def set_account_balance(balance: Dict[str, Any]):
    """계좌 정보 설정"""
    st.session_state.account_balance = balance

def get_account_balance() -> Optional[Dict[str, Any]]:
    """계좌 정보 반환"""
    return st.session_state.account_balance

def clear_session():
    """세션 데이터 초기화 (로그아웃)"""
    st.session_state.logged_in = False
    st.session_state.token = None
    st.session_state.user_info = None
    st.session_state.account_balance = None 