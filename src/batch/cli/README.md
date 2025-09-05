# Tools 폴더 - 배치 처리 도구들

이 폴더에는 애니메이션 메타데이터 자동 입력을 위한 배치 처리 및 관리 도구들이 있습니다.

## 🚀 주요 도구들

### 1. `batch_processor.py` - 배치 처리 실행
여러 애니메이션을 한 번에 처리하는 메인 스크립트입니다.

```bash
# 기본 사용법 (기본 노션 DB 사용)
python tools/batch_processor.py --csv anime.csv --description "첫 번째 25개 애니메이션"

# 다른 노션 데이터베이스 사용
python tools/batch_processor.py --csv anime.csv --db-id "새로운_DB_ID" --description "새 데이터베이스 테스트"

# 다른 CSV 파일 사용
python tools/batch_processor.py --csv anime_new50.csv --description "새로운 50개 애니메이션"
```

**결과**: `productions/YYYY-MM-DD_HHMMSS_파일명_batch/` 폴더에 체계적으로 저장

### 2. `check_status.py` - 배치 상태 확인
배치 처리 진행 상황과 결과를 확인합니다.

```bash
# 최신 배치 상태 확인
python tools/check_status.py

# 특정 배치 상태 확인
python tools/check_status.py --batch-id "2024-12-20_143000_anime_batch"

# 모든 배치 목록 보기
python tools/check_status.py --list

# 간단한 정보만 보기
python tools/check_status.py --brief
```

### 3. `resume_failed.py` - 실패 항목 재처리
실패한 애니메이션들만 골라서 다시 처리합니다.

```bash
# 최신 배치의 실패 항목 재처리
python tools/resume_failed.py

# 특정 배치의 실패 항목 재처리
python tools/resume_failed.py --batch-id "2024-12-20_143000_anime_batch"

# 실제 실행 없이 실패 항목만 확인
python tools/resume_failed.py --dry-run

# 특정 애니메이션만 재처리
python tools/resume_failed.py --item "스파이 패밀리"
```

## 📁 결과 폴더 구조

배치 처리 실행 후 다음과 같은 구조로 결과가 저장됩니다:

```
productions/
└── 2024-12-20_143000_anime_batch/
    ├── batch_config.json      # 배치 설정 정보
    ├── batch_summary.json     # 실행 결과 요약
    ├── search_results/        # Step 1 검색 결과들
    │   ├── search_01_SPY×FAMILY part 1.json
    │   ├── search_02_스크라이드.json
    │   └── ...
    ├── llm_results/          # Step 2 LLM 매칭 결과들
    │   ├── llm_01_SPY×FAMILY part 1.json
    │   ├── llm_02_스크라이드.json
    │   └── ...
    ├── metadata_results/     # Step 3 메타데이터 결과들
    │   ├── metadata_01_SPY×FAMILY part 1.json
    │   └── ...
    └── notion_results/       # Step 4 노션 업로드 결과들
        ├── notion_01_SPY×FAMILY part 1.json
        └── ...
```

## 💡 사용 시나리오

### 시나리오 1: 첫 번째 배치 처리 (25개)
```bash
# 1. 배치 실행
python tools/batch_processor.py --csv anime.csv --description "첫 번째 25개 애니메이션"

# 2. 결과 확인
python tools/check_status.py

# 3. 실패 항목이 있다면 재처리
python tools/resume_failed.py
```

### 시나리오 2: 새로운 애니메이션 목록 처리
```bash
# 1. 새 CSV 파일 준비 (anime_new50.csv)
# 2. 배치 실행
python tools/batch_processor.py --csv anime_new50.csv --description "새로운 50개 애니메이션"

# 3. 상태 확인
python tools/check_status.py
```

### 시나리오 3: 다른 노션 데이터베이스로 처리
```bash
# 1. 새 DB로 배치 실행
python tools/batch_processor.py --csv anime.csv --db-id "새로운_DB_ID" --description "새 데이터베이스"

# 2. 결과 확인
python tools/check_status.py
```

## ⚠️ 주의사항

1. **환경변수**: `.env` 파일에 `OPENAI_API_KEY`, `NOTION_TOKEN`, `NOTION_DATABASE_ID` 설정 필요
2. **비용**: OpenAI API 사용료 발생 (25개 애니메이션 ≈ $2-5)
3. **시간**: 전체 처리에 15-25분 소요
4. **중단**: `Ctrl+C`로 중단 가능 (처리된 항목은 저장됨)

## 🔧 문제 해결

### 실행 권한 오류
```bash
chmod +x tools/*.py
```

### 모듈 찾기 오류
프로젝트 루트 디렉토리에서 실행해주세요:
```bash
cd "/Users/jojo/프로젝트/애니메이션 메타데이터 자동 입력"
python tools/batch_processor.py --csv anime.csv
```

### API 오류
- OpenAI API 키 확인: `.env` 파일의 `OPENAI_API_KEY`
- 노션 토큰 확인: `.env` 파일의 `NOTION_TOKEN`
- 노션 DB ID 확인: `.env` 파일의 `NOTION_DATABASE_ID`
