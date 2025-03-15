# Kairos - 헤르메스(Hermes) | 실시간 퀀트 트레이딩 플랫폼 (프론트엔드)

이 프로젝트는 Kairos 퀀트 트레이딩 플랫폼의 프론트엔드 부분인 '헤르메스(Hermes)'입니다. Streamlit을 사용하여 개발되었습니다. Kairos는 그리스어로 '적절한 시기'를 의미하며, 트레이딩에서 가장 중요한 타이밍의 개념을 담고 있습니다. 헤르메스는 그리스 신화의 전령의 신으로, 사용자와 시스템 간의 소통을 담당하는 프론트엔드의 역할을 상징합니다.

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
python -m venv ~/.venvs/hermes  

# 또는 아나콘다/미니콘다 환경 사용
conda create -n hermes python=3.10 -y

# 가상환경 활성화 (Linux/Mac)
source ~/.venvs/hermes/bin/activate
# 또는 아나콘다/미니콘다 환경 활성화
conda activate hermes

# 가상환경 활성화 (Windows)
# .\~\.venvs\hermes\Scripts\activate.bat

# 의존성 패키지 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 프로젝트 루트 디렉토리에 생성하고 다음 내용을 추가합니다:

```
# API 서버 설정
API_URL=http://localhost:8000/api
```

`.env.example` 파일을 참고하여 필요한 환경 변수를 설정하세요.

**우분투 환경에서 .env 파일 생성 방법:**

```bash
# nano 에디터로 .env 파일 생성 및 편집
nano .env

# 편집 후 Ctrl+O를 눌러 저장, Ctrl+X로 나가기
# 또는 다음 명령으로 한 번에 생성
echo "API_URL=http://localhost:8000/api" > .env
```

### 3. 실행

가상환경이 활성화된 상태에서 다음 명령어로 프론트엔드 서버를 실행합니다:

```bash
# 첫 번째 방법 (권장) - run.py 스크립트 사용
python run.py

# 또는 다음 명령으로 스크립트 파일에 실행 권한 부여 후 직접 실행
chmod +x run.py
./run.py

# 두 번째 방법 - Streamlit 직접 실행
streamlit run app/main.py
```

기본적으로 서버는 http://localhost:8501 에서 실행됩니다.

### 4. 우분투 환경에서 포트 개방

방화벽이 활성화된 우분투 서버에서 실행하는 경우, 필요한 포트를 개방해야 합니다:

```bash
# Streamlit 서버 포트(8501) 개방
sudo ufw allow 8501/tcp

# 방화벽 상태 확인
sudo ufw status

# 방화벽이 비활성화된 경우 활성화
sudo ufw enable
```

클라우드 서버(AWS, GCP 등)에서 실행하는 경우, 해당 클라우드 서비스의 보안 그룹/방화벽 설정에서도 포트를 개방해야 합니다.

## 사용 방법

1. 브라우저에서 http://localhost:8501 에 접속합니다.
2. 로그인 페이지에서 사용자 계정으로 로그인합니다.
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