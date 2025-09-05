# 🚀 Render 배포 완전 가이드

> **대상**: API 서버 배포 초보자  
> **플랫폼**: Render.com 무료 플랜 (월 750시간)  
> **기술스택**: FastAPI + Python + GitHub

## 📋 배포 전 체크리스트

### ✅ 1. 필수 파일 확인
- [ ] `render.yaml` - Render 배포 설정
- [ ] `requirements-api.txt` - API 서버 의존성
- [ ] `env.example` - 환경변수 템플릿
- [ ] `src/api/main.py` - FastAPI 앱 엔트리포인트

### ✅ 2. GitHub 저장소 준비
- [ ] 모든 코드가 GitHub에 푸시됨
- [ ] main 브랜치가 최신 상태
- [ ] 민감한 정보(API 키)가 하드코딩되지 않음

## 🌐 Step 1: Render 계정 생성

### 1-1. 계정 생성
1. **[Render.com](https://render.com/)** 접속
2. **"Get Started"** 버튼 클릭
3. **GitHub으로 로그인** 선택 (가장 편리)
4. GitHub 계정 인증 완료

### 1-2. GitHub 저장소 권한 설정
- Render가 GitHub 저장소에 접근할 수 있도록 권한 부여
- 특정 저장소만 선택하거나 모든 저장소 권한 부여 선택

## ⚙️ Step 2: 웹 서비스 생성

### 2-1. 새 서비스 생성
1. Render 대시보드에서 **"New +"** 버튼 클릭
2. **"Web Service"** 선택
3. GitHub 저장소 선택:
   ```
   애니메이션 메타데이터 자동 입력
   ```

### 2-2. 기본 설정
| 설정 항목 | 값 | 설명 |
|-----------|----|----|
| **Name** | `anime-metadata-api` | 서비스 이름 (URL에 사용) |
| **Region** | `Singapore` | 한국과 가장 가까운 지역 |
| **Branch** | `main` | 배포할 브랜치 |
| **Root Directory** | (비움) | 프로젝트 루트 사용 |

### 2-3. 빌드 설정
| 설정 항목 | 값 |
|-----------|-----|
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements-api.txt` |
| **Start Command** | `python -m uvicorn src.api.main:app --host 0.0.0.0 --port $PORT` |

### 2-4. 플랜 선택
- **Free Plan** 선택
- **월 750시간 무료** (개인 프로젝트에 충분)
- 15분 비활성 시 슬립 모드

## 🔐 Step 3: 환경변수 설정

### 3-1. 환경변수 추가
**Advanced** 섹션에서 환경변수 설정:

| 키 | 값 | 설명 |
|----|----|----|
| `OPENAI_API_KEY` | `sk-proj-...` | OpenAI API 키 |
| `OPENAI_ASSISTANT_ID` | `asst_...` | Assistant ID |
| `NOTION_TOKEN` | `secret_...` | Notion API 토큰 |
| `NOTION_DATABASE_ID` | `a1b2c3d4...` | Notion 데이터베이스 ID |
| `LOG_LEVEL` | `INFO` | 로그 레벨 |

### 3-2. 자동 설정되는 환경변수
- `PORT` - Render가 자동으로 할당 (보통 10000)
- `RENDER` - Render 환경임을 나타내는 플래그

## 🚀 Step 4: 배포 실행

### 4-1. 서비스 생성
1. **"Create Web Service"** 버튼 클릭
2. 자동 빌드 및 배포 시작
3. 로그를 통해 진행 상황 확인

### 4-2. 배포 로그 확인
```bash
# 예상되는 빌드 로그
==> Installing dependencies from requirements-api.txt
==> Starting deployment
==> Running: python -m uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:10000
```

### 4-3. 배포 완료 확인
- **Live** 상태가 되면 배포 완료
- 제공된 URL (예: `https://anime-metadata-api.onrender.com`) 확인

## 🧪 Step 5: 배포 테스트

### 5-1. 헬스체크 테스트
```bash
curl https://your-app.onrender.com/health
```

**예상 응답:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.123Z"
}
```

### 5-2. API 엔드포인트 테스트
```bash
curl -X POST https://your-app.onrender.com/api/v1/process-anime \
  -H "Content-Type: application/json" \
  -d '{"title": "스파이 패밀리"}'
```

## 🔄 Step 6: 자동 배포 설정

### 6-1. GitHub 연동 확인
- `render.yaml`에 `autoDeploy: true` 설정으로 자동 배포 활성화
- main 브랜치에 push시 자동으로 재배포됨

### 6-2. 배포 알림 설정 (선택적)
1. Render 대시보드 → Settings → Notifications
2. 이메일 또는 Slack 연동 설정
3. 배포 성공/실패 알림 활성화

## ⚠️ 제약사항 및 주의사항

### 🆓 무료 플랜 제한사항 (2024년 기준)
- **월 750시간** (약 31일 * 24시간 = 744시간)
- **15분 비활성 시 슬립** → 첫 요청에 콜드 스타트 지연 (10-30초)
- **대역폭 제한**: 월 100GB
- **빌드 시간 제한**: 빌드당 최대 15분

### 🐛 자주 발생하는 문제들

#### 문제 1: 빌드 실패
**원인**: requirements-api.txt 의존성 문제
```bash
ERROR: Could not find a version that satisfies the requirement
```
**해결책**:
- Python 버전 호환성 확인
- requirements-api.txt 의존성 버전 조정

#### 문제 2: 시작 실패
**원인**: 시작 명령어 오류
```bash
ModuleNotFoundError: No module named 'src'
```
**해결책**:
- 시작 명령어 확인: `python -m uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
- 파일 구조가 올바른지 확인

#### 문제 3: 환경변수 오류
**원인**: API 키 설정 누락
```bash
KeyError: 'OPENAI_API_KEY'
```
**해결책**:
- Render 대시보드에서 환경변수 재확인
- 환경변수 추가 후 수동 재배포

#### 문제 4: 콜드 스타트 지연
**원인**: 15분 비활성 후 슬립
**해결책**:
- 정상적인 현상 (첫 요청에 10-30초 지연)
- 필요시 ping 서비스 사용해서 주기적 호출

## 📊 모니터링 및 로그

### 실시간 로그 확인
1. Render 대시보드 → 서비스 선택
2. **"Logs"** 탭 클릭
3. 실시간 로그 스트림 확인

### 성능 모니터링
- **Metrics** 탭에서 CPU, 메모리 사용량 확인
- 응답 시간 및 요청 수 모니터링

## 🔧 로컬 개발 vs Render 환경

### 로컬 개발 실행
```bash
# 로컬에서 API 서버 실행
python -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

### Render 환경 차이점
| 항목 | 로컬 | Render |
|------|------|--------|
| **포트** | 8000 | 환경변수 $PORT (보통 10000) |
| **호스트** | 127.0.0.1 | 0.0.0.0 |
| **리로드** | --reload | 사용하지 않음 |
| **로그** | 터미널 | Render 대시보드 |

## 🎯 다음 단계

배포 완료 후:
1. **아이폰 단축어 설정** → `docs/iphone-shortcut.md` 참조
2. **실제 테스트** → 애니메이션 제목으로 전체 플로우 테스트
3. **에러 모니터링** → Render 로그 주기적 확인

---

**💡 Tip**: 배포 후 첫 24시간은 로그를 주의깊게 관찰해서 예상치 못한 에러가 없는지 확인하세요!
