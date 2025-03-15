# Kairos - 아트라스(Atlas) | 실시간 퀀트 트레이딩 플랫폼 (백엔드)

이 프로젝트는 Kairos 퀀트 트레이딩 플랫폼의 백엔드 부분인 '아트라스(Atlas)'입니다. FastAPI를 사용하여 개발되었습니다. Kairos는 그리스어로 '적절한 시기'를 의미하며, 트레이딩에서 가장 중요한 타이밍의 개념을 담고 있습니다. 아트라스는 그리스 신화에서 하늘을 떠받치는 타이탄으로, 전체 시스템의 기반을 지지하는 백엔드의 역할을 상징합니다.

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
python -m venv ~/.venvs/atlas

# 또는 아나콘다/미니콘다 환경 사용
conda create -n atlas python=3.10 -y

# 가상환경 활성화 (Linux/Mac)
source ~/.venvs/atlas/bin/activate
# 또는 아나콘다/미니콘다 환경 활성화
conda activate atlas

# 가상환경 활성화 (Windows)
# .\~\.venvs\atlas\Scripts\activate.bat

# 의존성 패키지 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 프로젝트 루트 디렉토리에 생성하고 필요한 환경 변수를 설정합니다. `.env.example` 파일을 참고하세요.

**우분투 환경에서 .env 파일 생성 방법:**

```bash
# nano 에디터로 .env 파일 생성 및 편집
nano .env

# 편집 후 Ctrl+O를 눌러 저장, Ctrl+X로 나가기
# 또는 .env.example을 복사해서 설정
cp .env.example .env
nano .env  # 값을 수정하세요
```

### 3. 사용자 관리 (admin.py)

백엔드는 사용자 관리를 위한 별도의 CLI 도구(`admin.py`)를 제공합니다. 이 도구를 사용하여 새로운 사용자를 등록하거나, 비밀번호를 변경하거나, 사용자를 삭제할 수 있습니다.

```bash
# 가상환경 활성화 상태에서 실행

# 사용자 생성
python admin.py create -u 사용자명
# 관리자 사용자 생성
python admin.py create -u 관리자명 --admin

# 비밀번호 변경
python admin.py passwd -u 사용자명

# 사용자 삭제
python admin.py delete -u 사용자명

# 사용자 목록 조회
python admin.py list
```

특정 명령어에 대한 도움말은 다음과 같이 확인할 수 있습니다:

```bash
# 전체 명령어 도움말
python admin.py --help

# 특정 명령어 도움말 (예: create)
python admin.py create --help
```

사용자 데이터는 `~/.quant_trading_backend/users.json` 파일에 안전하게 저장됩니다. 비밀번호는 PBKDF2 알고리즘과 SHA-256 해시 함수를 사용하여 안전하게 해싱됩니다.

### 4. 실행

가상환경이 활성화된 상태에서 다음 명령어로 백엔드 서버를 실행합니다:

```bash
# 첫 번째 방법 (권장) - run.py 스크립트 사용
python run.py

# 또는 다음 명령으로 스크립트 파일에 실행 권한 부여 후 직접 실행
chmod +x run.py
./run.py

# 두 번째 방법 - uvicorn 직접 실행
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

기본적으로 서버는 http://localhost:8000 에서 실행됩니다.
API 문서는 http://localhost:8000/api/docs 에서 확인할 수 있습니다.

### 5. 우분투 환경에서 포트 개방

방화벽이 활성화된 우분투 서버에서 실행하는 경우, 필요한 포트를 개방해야 합니다:

```bash
# FastAPI 서버 포트(8000) 개방
sudo ufw allow 8000/tcp

# 방화벽 상태 확인
sudo ufw status

# 방화벽이 비활성화된 경우 활성화
sudo ufw enable
```

클라우드 서버(AWS, GCP 등)에서 실행하는 경우, 해당 클라우드 서비스의 보안 그룹/방화벽 설정에서도 포트를 개방해야 합니다.

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
├── admin.py           # 사용자 관리 CLI 도구
├── main.py            # 애플리케이션 엔트리 포인트
├── run.py             # 실행 스크립트
└── requirements.txt   # 필요한 패키지 목록
```

## 주의사항

- 실제 자산이 거래될 수 있으므로 신중하게 사용하세요.
- API 키는 타인에게 노출되지 않도록 주의하세요.
- 한국투자증권 API는 요청 제한이 있으므로 과도한 요청을 피하세요. 