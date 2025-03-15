# Kairos - 실시간 퀀트 트레이딩 플랫폼 (프론트엔드)

이 프로젝트는 Kairos 퀀트 트레이딩 플랫폼의 프론트엔드 부분으로, Streamlit을 사용하여 개발되었습니다. Kairos는 그리스어로 '적절한 시기'를 의미하며, 트레이딩에서 가장 중요한 타이밍의 개념을 담고 있습니다.

## 기능

- 사용자 로그인 및 인증
- 계좌 정보 및 잔고 조회
- 포트폴리오 시각화 (파이 차트, 손익 차트)
- 보유 종목 목록 표시
- 자동화된 거래 전략 설정 및 관리

## 설치 및 실행 방법

### 1. 가상환경 설정

가상환경은 프로젝트 외부에서 관리하는 것을 권장합니다. 다음과 같이 설정할 수 있습니다:

```bash
# 가상환경 생성 (위치는 사용자 선택)
python -m venv ~/.venvs/kairos-frontend  

# 가상환경 활성화 (Linux/Mac)
source ~/.venvs/kairos-frontend/bin/activate

# 가상환경 활성화 (Windows)
# .\~\.venvs\kairos-frontend\Scripts\activate.bat

# 의존성 패키지 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 프로젝트 루트 디렉토리에 생성하고 다음 내용을 추가합니다:

```
# API 서버 설정
API_URL=http://localhost:8000/api
KIS_APP_KEY=your_app_key_here
KIS_APP_SECRET=your_app_secret_here
```

### 3. 실행

가상환경이 활성화된 상태에서 다음 명령어로 프론트엔드 서버를 실행합니다:

```bash
python run.py
```

기본적으로 서버는 http://localhost:8501 에서 실행됩니다.

## 사용 방법

1. 브라우저에서 http://localhost:8501 에 접속합니다.
2. 로그인 페이지에서 한국투자증권 앱키와 시크릿을 입력합니다.
3. 로그인 후 계좌 정보 페이지에서 보유 종목과 계좌 잔고를 확인할 수 있습니다.

## 프로젝트 구조

```
frontend/
├── app/
│   ├── api/           # API 클라이언트
│   ├── components/    # UI 컴포넌트
│   ├── pages/         # 페이지 컴포넌트
│   └── utils/         # 유틸리티 함수
├── .env               # 환경 변수 파일
├── requirements.txt   # 필요한 패키지 목록
└── run.py             # 실행 스크립트
```

## 주의사항

- 실제 자산이 거래될 수 있으므로 신중하게 사용하세요.
- API 키는 타인에게 노출되지 않도록 주의하세요.
- 시장 상황에 따라 거래가 지연될 수 있습니다. 