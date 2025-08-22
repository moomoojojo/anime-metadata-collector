# 🎬 애니메이션 메타데이터 자동 입력 시스템

OpenAI Assistant와 라프텔 API를 활용한 스마트 애니메이션 매칭 및 노션 자동화 시스템

## 🏗️ 시스템 구조

### **핵심 파이프라인**
```
1단계 → 2단계 → 3단계 → 4단계
검색   → 매칭   → 수집   → 업로드
```

| 단계 | 파일 | 기능 |
|---|---|---|
| **1단계** | `step1_search_candidates.py` | 라프텔 검색 + 검색어 전처리 |
| **2단계** | `step2_llm_matching.py` | OpenAI Assistant 스마트 매칭 |
| **3단계** | `step3_metadata_collection.py` | 상세 메타데이터 수집 |
| **4단계** | `step4_notion_upload.py` | 노션 데이터베이스 업로드 |

## 📁 폴더 구조

```
📦 애니메이션 메타데이터 자동 입력/
├── 📄 config.py                    # 설정 파일
├── 📄 step1_search_candidates.py   # 1단계: 라프텔 검색
├── 📄 step2_llm_matching.py        # 2단계: OpenAI 매칭
├── 📄 step3_metadata_collection.py # 3단계: 메타데이터 수집
├── 📄 step4_notion_upload.py       # 4단계: 노션 업로드
├── 📄 anime.csv                    # 입력 데이터
├── 📄 .env                         # 환경변수 (API 키)
├── 📁 results/                     # 결과 파일들
├── 📁 tests/                       # 테스트 파일들
├── 📁 legacy/                      # 기존 A단계 파일들
└── 📁 archive/                     # 개발 과정 파일들
```

## ⚙️ 주요 기능

### **🔧 검색어 전처리**
- "스파이 패밀리 1기" → "스파이 패밀리" (검색 최적화)
- 시즌 정보 제거로 검색 성공률 향상

### **🤖 OpenAI 스마트 매칭**
- 70% 이상 유사도 기준
- 자막판 우선 선택
- 매칭 불가 시 안전한 거부

### **📊 메타데이터 수집**
- 8개 필드: 제목, 방영분기, 평점, 상태, URL, 제작사, 화수
- 조건부 실행 (2단계 성공 시에만)

## 📋 노션 데이터베이스 칼럼

| 칼럼명 | 노션 타입 | 설명 |
|---|---|---|
| **입력 제목** | Rich Text | 사용자 최초 입력 |
| **제목** | Title | 실제 매칭된 제목 |
| **방영분기** | Rich Text | 방영 시기 |
| **라프텔 평점** | Number | 평점 (소수점) |
| **상태** | Select | "완결" 또는 "방영중" |
| **라프텔 URL** | URL | 라프텔 링크 |
| **커버 URL** | URL | 포스터 이미지 |
| **제작사** | Select | 제작 스튜디오 |
| **총 화수** | Number | 에피소드 수 |

## 🔑 환경 설정

### **.env 파일**
```bash
# OpenAI API
OPENAI_API_KEY=sk-proj-xxxxx
OPENAI_ASSISTANT_ID=asst_xxxxx

# Notion API  
NOTION_TOKEN=ntn_xxxxx
NOTION_DATABASE_ID=xxxxx-xxxxx-xxxxx
```

## 🚀 사용법

### **개별 실행**
```bash
python3 step1_search_candidates.py
python3 step2_llm_matching.py  
python3 step3_metadata_collection.py
python3 step4_notion_upload.py
```

### **전체 파이프라인 테스트**
```bash
python3 tests/test_full_pipeline_1_to_3.py
```

## 📈 성능 지표

- ✅ **전체 성공률**: 4/4 (100%)
- ✅ **3단계 성공률**: 4/4 (100%)
- ✅ **자막판 우선 선택**: 작동
- ✅ **검색어 전처리 효과**: 75% 케이스에서 적용

## 🧪 테스트 케이스

| 입력 | 결과 | 신뢰도 |
|---|---|---|
| "Re: 제로부터 시작하는 이세계 생활 3기" | ✅ 매칭 성공 | 98% |
| "스파이 패밀리 1기" | ✅ 매칭 성공 (자막판) | 95% |
| "무직전생 1기" | ✅ 매칭 성공 | 95% |
| "스크라이드" | ✅ 매칭 성공 | 95% |

## 📝 개발 로그

- ✅ 1-3단계 구현 완료
- ✅ 검색어 전처리 추가
- ✅ 자막판 우선 정책 구현
- ✅ MAX_SEARCH_CANDIDATES 20개로 확장
- ✅ 4단계 노션 업로드 구현 완료
- ✅ GitHub 저장소 연결 및 보안 설정 완료
- 🎯 **새로운 기능**: Git 변화 추적 및 Cursor 통합 테스트

---

*Created with ❤️ using OpenAI Assistant & Laftel API*
