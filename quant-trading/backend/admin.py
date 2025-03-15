#!/usr/bin/env python
import argparse
import os
import json
import getpass
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import secrets
import hashlib
import base64

# 사용자 데이터 저장 경로
USERS_DIR = Path.home() / ".quant_trading_backend"
USERS_FILE = USERS_DIR / "users.json"

def secure_hash_password(password: str, salt: Optional[str] = None) -> Dict[str, str]:
    """
    안전한 비밀번호 해싱 (PBKDF2 with SHA-256)
    
    Args:
        password: 해싱할 비밀번호
        salt: 솔트 (없으면 자동 생성)
        
    Returns:
        {'hash': 해시값, 'salt': 솔트, 'iterations': 반복 횟수}
    """
    # 솔트가 없으면 생성
    if not salt:
        salt = secrets.token_hex(16)
    
    # 반복 횟수 (높을수록 보안성 증가)
    iterations = 100000
    
    # PBKDF2 해싱
    hash_value = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt.encode('utf-8'), 
        iterations
    )
    
    # base64로 인코딩하여 반환
    hash_b64 = base64.b64encode(hash_value).decode('utf-8')
    
    return {
        'hash': hash_b64,
        'salt': salt,
        'iterations': iterations
    }

def verify_password(password: str, password_data: Dict[str, Any]) -> bool:
    """
    비밀번호 검증
    
    Args:
        password: 검증할 비밀번호
        password_data: 저장된 비밀번호 데이터 {'hash': 해시값, 'salt': 솔트, 'iterations': 반복 횟수}
        
    Returns:
        검증 결과 (True/False)
    """
    hash_to_verify = secure_hash_password(
        password, 
        salt=password_data['salt']
    )
    
    return hash_to_verify['hash'] == password_data['hash']

def load_users() -> Dict[str, Any]:
    """사용자 데이터 로드"""
    if not os.path.exists(USERS_FILE):
        return {}
    
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"사용자 데이터 로드 중 오류 발생: {str(e)}")
        return {}

def save_users(users: Dict[str, Any]) -> None:
    """사용자 데이터 저장"""
    # 디렉토리 생성
    os.makedirs(USERS_DIR, exist_ok=True)
    
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        print(f"사용자 데이터 저장 중 오류 발생: {str(e)}")

def create_user(username: str, password: str, is_admin: bool = False) -> bool:
    """
    새 사용자 생성
    
    Args:
        username: 사용자 아이디
        password: 비밀번호
        is_admin: 관리자 여부
        
    Returns:
        성공 여부
    """
    # 사용자 데이터 로드
    users = load_users()
    
    # 이미 존재하는 사용자인지 확인
    if username in users:
        print(f"오류: 사용자 '{username}'은(는) 이미 존재합니다.")
        return False
    
    # 비밀번호 해싱
    password_data = secure_hash_password(password)
    
    # 사용자 추가
    users[username] = {
        "password_data": password_data,
        "created_at": datetime.now().isoformat(),
        "is_admin": is_admin
    }
    
    # 저장
    save_users(users)
    print(f"사용자 '{username}'이(가) 추가되었습니다." + (" (관리자)" if is_admin else ""))
    return True

def update_password(username: str, new_password: str) -> bool:
    """
    사용자 비밀번호 변경
    
    Args:
        username: 사용자 아이디
        new_password: 새 비밀번호
        
    Returns:
        성공 여부
    """
    # 사용자 데이터 로드
    users = load_users()
    
    # 존재하는 사용자인지 확인
    if username not in users:
        print(f"오류: 사용자 '{username}'이(가) 존재하지 않습니다.")
        return False
    
    # 비밀번호 해싱
    password_data = secure_hash_password(new_password)
    
    # 비밀번호 업데이트
    users[username]["password_data"] = password_data
    users[username]["updated_at"] = datetime.now().isoformat()
    
    # 저장
    save_users(users)
    print(f"사용자 '{username}'의 비밀번호가 변경되었습니다.")
    return True

def delete_user(username: str) -> bool:
    """
    사용자 삭제
    
    Args:
        username: 삭제할 사용자 아이디
        
    Returns:
        성공 여부
    """
    # 사용자 데이터 로드
    users = load_users()
    
    # 존재하는 사용자인지 확인
    if username not in users:
        print(f"오류: 사용자 '{username}'이(가) 존재하지 않습니다.")
        return False
    
    # 삭제
    del users[username]
    
    # 저장
    save_users(users)
    print(f"사용자 '{username}'이(가) 삭제되었습니다.")
    return True

def list_users() -> None:
    """사용자 목록 출력"""
    users = load_users()
    
    if not users:
        print("등록된 사용자가 없습니다.")
        return
    
    print(f"\n{'=' * 60}")
    print(f"{'사용자명':<20} {'생성일시':<25} {'관리자':<10}")
    print(f"{'-' * 60}")
    
    for username, data in users.items():
        created_at = data.get("created_at", "N/A")
        is_admin = "예" if data.get("is_admin", False) else "아니오"
        print(f"{username:<20} {created_at:<25} {is_admin:<10}")
    
    print(f"{'=' * 60}")
    print(f"총 {len(users)}명의 사용자가 등록되어 있습니다.\n")

def main():
    parser = argparse.ArgumentParser(description='퀀트 트레이딩 API 사용자 관리 도구')
    subparsers = parser.add_subparsers(dest='command', help='명령어')
    
    # 사용자 생성 명령어
    create_parser = subparsers.add_parser('create', help='새 사용자 생성 (일반 사용자는 -u 사용자명, 관리자는 -u 사용자명 --admin)')
    create_parser.add_argument('--username', '-u', required=True, help='사용자 아이디')
    create_parser.add_argument('--password', '-p', help='비밀번호 (입력하지 않으면 프롬프트로 요청)')
    create_parser.add_argument('--admin', '-a', action='store_true', help='관리자 권한 부여')
    
    # 비밀번호 변경 명령어
    passwd_parser = subparsers.add_parser('passwd', help='사용자 비밀번호 변경 (-u 사용자명)')
    passwd_parser.add_argument('--username', '-u', required=True, help='사용자 아이디')
    passwd_parser.add_argument('--password', '-p', help='새 비밀번호 (입력하지 않으면 프롬프트로 요청)')
    
    # 사용자 삭제 명령어
    delete_parser = subparsers.add_parser('delete', help='사용자 삭제 (-u 사용자명)')
    delete_parser.add_argument('--username', '-u', required=True, help='삭제할 사용자 아이디')
    
    # 사용자 목록 명령어
    list_parser = subparsers.add_parser('list', help='등록된 모든 사용자 목록 출력')
    
    args = parser.parse_args()
    
    # 명령어 처리
    if args.command == 'create':
        password = args.password
        if not password:
            password = getpass.getpass("비밀번호: ")
            confirm = getpass.getpass("비밀번호 확인: ")
            if password != confirm:
                print("오류: 비밀번호가 일치하지 않습니다.")
                return
        
        create_user(args.username, password, args.admin)
        
    elif args.command == 'passwd':
        password = args.password
        if not password:
            password = getpass.getpass("새 비밀번호: ")
            confirm = getpass.getpass("비밀번호 확인: ")
            if password != confirm:
                print("오류: 비밀번호가 일치하지 않습니다.")
                return
        
        update_password(args.username, password)
        
    elif args.command == 'delete':
        confirm = input(f"정말로 사용자 '{args.username}'을(를) 삭제하시겠습니까? (y/n): ")
        if confirm.lower() == 'y':
            delete_user(args.username)
        
    elif args.command == 'list':
        list_users()
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 