# Kairos - 실시간 퀀트 트레이딩 플랫폼 (백엔드)

이 프로젝트는 Kairos 퀀트 트레이딩 플랫폼의 백엔드 부분으로, FastAPI를 사용하여 개발되었습니다. Kairos는 그리스어로 '적절한 시기'를 의미하며, 트레이딩에서 가장 중요한 타이밍의 개념을 담고 있습니다.

## 기능

- 한국투자증권 Open Trading API 연동
- 사용자 인증 및 토큰 관리
- 계좌 정보 및 잔고 조회 API
- 토큰 캐싱 및 재사용 기능
- 확장 가능한 다중 브로커 API 구조
- 자동화된 거래 실행 엔진

## 설치 및 실행 방법

### 1. 가상환경 설정

가상환경은 프로젝트 외부에서 관리하는 것을 권장합니다. 다음과 같이 설정할 수 있습니다:

```bash
# 가상환경 생성 (위치는 사용자 선택)
python -m venv ~/.venvs/kairos-backend

# 가상환경 활성화 (Linux/Mac)
source ~/.venvs/kairos-backend/bin/activate

# 가상환경 활성화 (Windows)
# .\~\.venvs\kairos-backend\Scripts\activate.bat

# 의존성 패키지 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 프로젝트 루트 디렉토리에 생성하고 필요한 환경 변수를 설정합니다. `.env.example` 파일을 참고하세요.

### 3. 실행

가상환경이 활성화된 상태에서 다음 명령어로 백엔드 서버를 실행합니다:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

기본적으로 서버는 http://localhost:8000 에서 실행됩니다.
API 문서는 http://localhost:8000/api/docs 에서 확인할 수 있습니다.

## 프로젝트 구조

```
backend/
├── app/
│   ├── api/           # API 엔드포인트
│   ├── core/          # 코어 설정 및 보안
│   ├── models/        # 데이터 모델
│   ├── schemas/       # 데이터 스키마
│   ├── services/      # 비즈니스 로직
│   └── utils/         # 유틸리티 함수
├── .env               # 환경 변수 파일
├── main.py            # 애플리케이션 엔트리 포인트
└── requirements.txt   # 필요한 패키지 목록
```

## 주의사항

- 실제 자산이 거래될 수 있으므로 신중하게 사용하세요.
- API 키는 타인에게 노출되지 않도록 주의하세요.
- 한국투자증권 API는 요청 제한이 있으므로 과도한 요청을 피하세요. 