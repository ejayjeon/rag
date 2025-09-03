# 🤖 OpenAI API 키 설정 가이드

이 문서는 멀티모달 RAG 시스템에서 OpenAI API를 사용하기 위한 설정 방법을 설명합니다.

## 📋 OpenAI API 키 설정 방법

### 방법 1: 환경변수 설정 (권장)

#### 1️⃣ macOS/Linux
```bash
# 터미널에서 실행
export OPENAI_API_KEY="sk-your-api-key-here"

# 영구 설정 (bash)
echo 'export OPENAI_API_KEY="sk-your-api-key-here"' >> ~/.bashrc
source ~/.bashrc

# 영구 설정 (zsh)
echo 'export OPENAI_API_KEY="sk-your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

#### 2️⃣ Windows
```cmd
# 명령 프롬프트에서 실행
set OPENAI_API_KEY=sk-your-api-key-here

# PowerShell에서 실행
$env:OPENAI_API_KEY="sk-your-api-key-here"

# 시스템 환경변수로 영구 설정
setx OPENAI_API_KEY "sk-your-api-key-here"
```

#### 3️⃣ .env 파일 사용
```bash
# 프로젝트 루트에 .env 파일 생성
cp .env.example .env

# .env 파일 편집
echo "OPENAI_API_KEY=sk-your-api-key-here" > .env
```

### 방법 2: Streamlit 앱에서 직접 입력

1. **Streamlit 앱 실행**: `streamlit run streamlit_app.py`
2. **OpenAI 선택**: 사이드바에서 "openai" 프로바이더 선택
3. **API 키 입력**: 텍스트 입력창에 API 키 입력
4. **자동 검증**: 실시간으로 키 유효성 확인

## 🔑 OpenAI API 키 발급 방법

1. **OpenAI 계정 생성**: [platform.openai.com](https://platform.openai.com) 방문
2. **로그인**: 계정 로그인 또는 신규 가입
3. **API 키 생성**: 
   - API Keys 메뉴로 이동
   - "Create new secret key" 클릭
   - 키 이름 입력 후 생성
   - **중요**: 생성된 키를 안전한 곳에 저장 (다시 볼 수 없음)

## 💰 비용 정보

### OpenAI API 사용료
- **GPT-3.5-turbo** (텍스트): $0.0015 / 1K tokens (입력), $0.002 / 1K tokens (출력)
- **GPT-4-vision** (이미지 분석): $0.01 / 1K tokens (입력), $0.03 / 1K tokens (출력)
- **이미지 처리**: 이미지 크기에 따라 추가 비용

### 예상 사용량
- **문서 1개 처리**: 약 $0.01-0.05
- **이미지 1개 분석**: 약 $0.02-0.10
- **질문 1개 답변**: 약 $0.001-0.01

## 🛡️ 보안 주의사항

### ✅ 권장사항
- API 키를 환경변수나 .env 파일에 저장
- .env 파일을 .gitignore에 추가
- API 키 사용량 모니터링
- 정기적으로 키 순환 (rotation)

### ❌ 금지사항
- 코드에 직접 하드코딩 금지
- 공개 저장소에 커밋 금지
- 다른 사람과 키 공유 금지
- 의심스러운 활동 시 즉시 키 비활성화

## 🔧 트러블슈팅

### 문제 1: "API 키가 유효하지 않습니다"
- API 키 형식 확인 (`sk-`로 시작하는지)
- 키 복사 시 공백이나 특수문자 포함 여부 확인
- OpenAI 대시보드에서 키 상태 확인

### 문제 2: "권한이 부족합니다"
- 계정에 충분한 크레딧이 있는지 확인
- API 키에 필요한 권한이 부여되었는지 확인
- 사용량 제한 설정 확인

### 문제 3: "요청 한도 초과"
- API 사용량이 제한을 초과했는지 확인
- 잠시 후 다시 시도
- 필요시 OpenAI에 한도 증가 요청

### 문제 4: 환경변수가 인식되지 않음
```bash
# 환경변수 설정 확인
echo $OPENAI_API_KEY

# 새 터미널 세션에서 다시 시도
# 또는 앱을 재시작
```

## 📱 앱 사용 흐름

### 환경변수 사용시
1. 터미널에서 환경변수 설정
2. `streamlit run streamlit_app.py` 실행
3. OpenAI 선택
4. ✅ "환경변수 API 키 사용" 자동 체크됨
5. 자동 검증 완료 후 바로 사용 가능

### 수동 입력시
1. `streamlit run streamlit_app.py` 실행
2. OpenAI 선택
3. "OpenAI API Key" 필드에 키 입력
4. 실시간 검증 후 사용 가능

## 🌟 장점 비교

| 방법 | 장점 | 단점 |
|------|------|------|
| 환경변수 | 자동 로드, 보안성, 편의성 | 초기 설정 필요 |
| 수동 입력 | 즉시 사용 가능 | 매번 입력 필요 |
| .env 파일 | 프로젝트별 관리, 버전 관리 | 파일 보안 관리 필요 |

## 💡 추천 설정

**개발자/고급 사용자**:
```bash
# 환경변수 + .env 파일 조합
export OPENAI_API_KEY="sk-your-key"
echo "OPENAI_API_KEY=sk-your-key" > .env
```

**일반 사용자**:
- Streamlit 앱에서 직접 입력 사용
- 보안을 위해 사용 후 브라우저 시크릿 모드 권장