# Kairos - 실시간 퀀트 트레이딩 플랫폼

![Kairos Banner](https://capsule-render.vercel.app/api?type=waving&color=gradient&height=200&section=header&text=Kairos&fontSize=70&animation=fadeIn&fontAlignY=38&desc=실시간%20퀀트%20트레이딩%20플랫폼&descAlignY=55&descAlign=62)

## 🚀 프로젝트 소개

**Kairos**(καιρός)는 그리스어로 '적절한 시기', '결정적인 순간'을 의미합니다. 금융 시장에서 타이밍은 모든 것이며, Kairos는 그 결정적인 순간을 포착하여 투자자에게 최적의 트레이딩 기회를 제공하는 것을 목표로 합니다.

이 프로젝트는 [한국투자증권의 Open Trading API](https://github.com/koreainvestment/open-trading-api)를 활용한 실시간 퀀트 트레이딩 시스템으로, 사용자 친화적인 인터페이스와 강력한 백엔드 시스템을 통해 효율적인 트레이딩 환경을 제공합니다. 공식 API 예제와 문서를 참고하여 개발되었으며, 실제 트레이딩에 적합한 형태로 기능을 확장하였습니다.

프로젝트는 두 부분으로 구성됩니다:
- **아트라스(Atlas)**: 백엔드 시스템, FastAPI 기반으로 개발됨
- **헤르메스(Hermes)**: 프론트엔드 시스템, Streamlit 기반으로 개발됨

## ✨ 주요 기능

### 🔐 보안 강화된 인증 시스템
- 사용자 정보와 API 키를 안전하게 관리
- 백엔드에서 토큰 관리 및 갱신 자동화
- PBKDF2와 SHA-256을 활용한 안전한 비밀번호 해싱

### 📊 실시간 데이터 시각화
- 포트폴리오 구성 파이 차트
- 실시간 손익 모니터링
- 종목별 성과 분석

### 📈 계좌 관리
- 실시간 잔고 조회
- 보유 종목 상세 정보
- 매매 이력 추적

### 🤖 자동화된 거래 전략
- 사용자 정의 매매 전략 설정
- 시장 상황에 따른 자동 거래 실행
- 성과 분석 및 백테스팅

### 🌐 확장 가능한 아키텍처
- 다중 브로커 API 지원 구조
- 모듈식 설계로 새로운 기능 추가 용이
- 다양한 거래 시장 확장 가능

## 🛠️ 기술 스택

### 백엔드 (아트라스)
- **FastAPI**: 고성능 비동기 API 서버
- **JWT**: 보안 토큰 기반 인증
- **SQLAlchemy**: 데이터베이스 ORM
- **Pydantic**: 데이터 검증 및 설정 관리

### 프론트엔드 (헤르메스)
- **Streamlit**: 데이터 중심 대시보드
- **Plotly**: 인터랙티브 차트 및 시각화
- **Pandas**: 데이터 분석 및 처리

## 🚀 시작하기

### 사전 요구사항
- Python 3.8 이상
- 한국투자증권 계정 및 API 키 (실전 또는 모의투자)
- Linux, macOS 또는 Windows 환경

### 빠른 설치

```bash
# 저장소 클론
git clone https://github.com/restful3/Kairos.git
cd Kairos

# 백엔드 설정 및 실행
cd kairos/backend
python -m venv ~/.venvs/kairos-backend
source ~/.venvs/kairos-backend/bin/activate
pip install -r requirements.txt
python run.py

# 새 터미널에서 프론트엔드 설정 및 실행
cd kairos/frontend
python -m venv ~/.venvs/kairos-frontend
source ~/.venvs/kairos-frontend/bin/activate
pip install -r requirements.txt
python run.py
```

자세한 설치 및 설정 방법은 각 디렉토리의 README.md 파일을 참고하세요.

## 👥 사용자 관리

Kairos는 백엔드(아트라스)에서 관리자용 CLI 도구를 제공하여 사용자를 쉽게 관리할 수 있습니다:

```bash
# 백엔드 디렉토리에서
python admin.py create -u 사용자명      # 일반 사용자 생성
python admin.py create -u 관리자명 --admin  # 관리자 사용자 생성
python admin.py list                   # 사용자 목록 조회
python admin.py passwd -u 사용자명      # 비밀번호 변경
python admin.py delete -u 사용자명      # 사용자 삭제
```

모든 사용자 데이터는 `~/.quant_trading_backend/users.json` 파일에 안전하게 저장됩니다.

## 📝 환경 설정

`.env` 파일을 통해 API 키 및 기타 설정을 관리합니다:

1. 백엔드와 프론트엔드 디렉토리에 있는 `.env.example` 파일을 복사하여 `.env` 파일 생성
2. 필요한 설정값 입력 (API URL, 시크릿 키 등)

### 백엔드(아트라스) .env 설정
`.env.example` 파일을 참고하여 한국투자증권 API 키 및 기타 설정을 구성합니다.

### 프론트엔드(헤르메스) .env 설정
기본적인 설정은 다음과 같습니다:
```
# API 서버 설정
API_URL=http://localhost:8000/api
```

## 💡 프로젝트 구조

```
kairos/
├── backend/           # 아트라스(Atlas) - FastAPI 백엔드
│   ├── app/           # 애플리케이션 코드
│   │   ├── api/       # API 엔드포인트
│   │   ├── core/      # 핵심 기능 (설정, 보안)
│   │   ├── models/    # 데이터 모델
│   │   ├── schemas/   # 데이터 스키마  
│   │   ├── services/  # 비즈니스 로직
│   │   └── utils/     # 유틸리티 함수
│   ├── data/          # 데이터 저장소
│   ├── tests/         # 테스트 코드
│   ├── admin.py       # 관리자 CLI 도구
│   ├── main.py        # 메인 애플리케이션 진입점
│   ├── run.py         # 서버 실행 스크립트
│   ├── requirements.txt # 의존성 패키지 목록
│   └── .env.example   # 환경 변수 예시 파일
│
├── frontend/          # 헤르메스(Hermes) - Streamlit 프론트엔드
│   ├── app/           # 애플리케이션 코드
│   │   ├── components/# UI 컴포넌트
│   │   ├── pages/     # 페이지 정의
│   │   └── utils/     # 유틸리티 함수
│   ├── data/          # 데이터 저장소
│   ├── services/      # 서비스 로직
│   ├── stock_data/    # 주식 데이터
│   ├── tests/         # 테스트 코드
│   ├── run.py         # 서버 실행 스크립트
│   ├── requirements.txt # 의존성 패키지 목록
│   └── .env.example   # 환경 변수 예시 파일
│
└── docker-compose.yml # Docker 컴포즈 설정 파일
```

## ⚠️ 주의사항

- 이 프로젝트는 실제 자산을 거래할 수 있으므로 신중하게 사용하세요.
- API 키는 절대 공개 저장소에 커밋하지 마세요.
- 모의투자 환경에서 충분히 테스트한 후 실전 환경에서 사용하세요.
- 한국투자증권 API는 요청 제한이 있으므로 과도한 요청을 피하세요.

## 🔜 로드맵

- [X] 사용자 인증 및 토큰 관리 시스템
- [X] 기본 계좌 정보 및 잔고 조회
- [X] 포트폴리오 시각화
- [ ] 커스텀 트레이딩 전략 설정 인터페이스
- [ ] 복수 계좌 관리 기능
- [ ] 퍼포먼스 모니터링 대시보드
- [ ] 실시간 알림 시스템

## 📄 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 LICENSE 파일을 참조하세요.

## 🙏 감사의 말

이 프로젝트는 한국투자증권의 Open Trading API를 기반으로 구축되었습니다. [공식 API GitHub 저장소](https://github.com/koreainvestment/open-trading-api)와 [개발자 포털](https://apiportal.koreainvestment.com)에서 제공하는 예제 코드와 문서에 큰 도움을 받았습니다. 한국투자증권의 API 제공과 지속적인 업데이트에 감사드립니다.

## 📧 연락처

문의사항이나 기여를 원하시면 이슈를 생성하거나 Pull Request를 보내주세요.
