import streamlit as st
import os
from dotenv import load_dotenv

from app.api.client import api_client
from app.utils.session import set_logged_in, set_token, set_user_info

# 환경 변수 로드
load_dotenv()

def show():
    """로그인 페이지 표시"""
    
    st.title("Kairos 로그인")
    
    st.write("Kairos 트레이딩 플랫폼에 접속하기 위해 사용자 아이디와 비밀번호를 입력해주세요.")
    
    with st.form("login_form"):
        username = st.text_input("사용자 아이디")
        password = st.text_input("비밀번호", type="password")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            submitted = st.form_submit_button("로그인", use_container_width=True)
    
    # 로그인 처리
    if submitted:
        if not username or not password:
            st.error("사용자 아이디와 비밀번호를 모두 입력해주세요.")
            return
        
        with st.spinner("로그인 중..."):
            try:
                # 백엔드 API 로그인
                result = api_client.login(username, password)
                
                # 세션 상태 업데이트
                set_token(result["access_token"])
                set_logged_in(True)
                
                # 사용자 정보 조회
                try:
                    user_info = api_client.get_user_info()
                    set_user_info(user_info)
                except Exception as e:
                    st.warning(f"사용자 정보 조회 중 오류 발생: {str(e)}")
                    set_user_info({"username": username})
                
                st.success("로그인 성공!")
                st.rerun()  # 페이지 새로고침
            except Exception as e:
                st.error(f"로그인 실패: {str(e)}")
                
    # 안내 메시지
    with st.expander("사용자 계정 안내"):
        st.markdown("""
        ### Kairos 계정 정보
        
        관리자에게 문의하여 Kairos 사용자 계정을 발급받으세요.
        
        ### 관리자 계정 생성 방법 (관리자용)
        
        1. 서버에서 다음 명령어를 실행하여 관리자 계정을 생성할 수 있습니다:
           ```
           python admin.py create -u 관리자ID --admin
           ```
        
        2. 일반 사용자 계정 생성:
           ```
           python admin.py create -u 사용자ID
           ```
        
        ### 비밀번호 변경 방법
        
        관리자에게 문의하여 비밀번호를 재설정하세요.
        """) 