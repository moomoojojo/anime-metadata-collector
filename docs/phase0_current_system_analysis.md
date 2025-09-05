# Phase 0 현재 시스템 분석 문서

> **분석일**: 2025-09-05  
> **목적**: 리팩토링 전 현재 시스템의 의존성 및 구조 분석  
> **분석 대상**: 기존 배치 처리 시스템

## 📦 의존성 분석

### **requirements.txt**
```txt
# 핵심 라이브러리
openai>=1.0.0                    # OpenAI API (Assistant, GPT-4.1)
requests>=2.31.0                 # HTTP 요청 (Notion API)
python-dotenv>=1.0.0             # 환경변수 관리

# 라프텔 API (비공식)
laftel>=1.3.0                    # 라프텔 비공식 API 래퍼
aiohttp>=3.8.0                   # laftel 의존성

# 표준 라이브러리 (별도 설치 불필요)
# json, os, re, csv, glob, argparse, subprocess
# datetime, typing, sys
```

### **의존성 역할**
- **openai**: OpenAI Assistant API 호출 (Step 2 AI 매칭)
- **requests**: Notion API HTTP 요청 (Step 4 노션 업로드)
- **python-dotenv**: .env 파일에서 환경변수 로드
- **laftel**: 라프텔 비공식 API 래퍼 (Step 1 검색, Step 3 메타데이터)
- **aiohttp**: laftel 라이브러리의 비동기 HTTP 요청 의존성

## 🏗️ 모듈 구조 분석

### **현재 파일 구조**
```
src/
├── __init__.py
└── anime_metadata/
    ├── __init__.py
    ├── config.py                    # 설정 및 환경변수 관리
    ├── step1_search_candidates.py   # 라프텔 검색
    ├── step2_llm_matching.py        # OpenAI Assistant 매칭
    ├── step3_metadata_collection.py # 메타데이터 수집  
    ├── step4_notion_upload.py       # 노션 업로드
    └── tools/
        ├── batch_processor.py       # 메인 배치 처리기
        ├── check_status.py          # 배치 상태 확인
        ├── resume_failed.py         # 실패 항목 재처리
        └── README.md
```

### **Import 경로 분석**

#### **batch_processor.py (메인 파일)**
```python
# 표준 라이브러리
import os, sys, csv, json, argparse, subprocess
from datetime import datetime
from typing import List, Dict, Any

# 외부 라이브러리  
import laftel

# 프로젝트 내부 모듈 (절대 경로)
from src.anime_metadata import step1_search_candidates
from src.anime_metadata import step2_llm_matching
from src.anime_metadata import step3_metadata_collection
from src.anime_metadata import step4_notion_upload
from src.anime_metadata import config
```

#### **각 step 파일들**
```python
# config.py
import os
from dotenv import load_dotenv

# step1_search_candidates.py  
import json, laftel, re
from datetime import datetime
from typing import List, Dict, Any
from . import config                 # 상대 경로
```

## 🔧 실행 방법 분석

### **현재 실행 방법**
```bash
# 필수: PYTHONPATH 설정
PYTHONPATH=. python3 src/anime_metadata/tools/batch_processor.py --csv file.csv --description "설명"
```

### **PYTHONPATH 필요 이유**
- `batch_processor.py`에서 `from src.anime_metadata import ...` 절대 경로 사용
- Python이 `src` 모듈을 찾을 수 있도록 프로젝트 루트를 PYTHONPATH에 추가 필요
- PYTHONPATH 없이 실행시: `ModuleNotFoundError: No module named 'src'`

### **대안 실행 방법들**
```bash
# 방법 1: PYTHONPATH 설정 (현재 동작 확인됨)
PYTHONPATH=. python3 src/anime_metadata/tools/batch_processor.py

# 방법 2: 모듈 실행 방식 (미확인)
python3 -m src.anime_metadata.tools.batch_processor

# 방법 3: sys.path 수정 (batch_processor.py 내부에서 이미 시도)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
```

## 🌊 데이터 플로우 분석

### **4단계 파이프라인**
1. **Step 1**: `step1_search_candidates.py`
   - laftel API로 애니메이션 검색
   - 최대 20개 후보 수집
   - JSON 파일로 결과 저장

2. **Step 2**: `step2_llm_matching.py`  
   - OpenAI Assistant API 호출
   - 사용자 입력과 후보군 매칭
   - 최적 매칭 결과 선택

3. **Step 3**: `step3_metadata_collection.py`
   - 선택된 애니메이션의 상세 메타데이터 수집
   - 라프텔 API로 추가 정보 획득

4. **Step 4**: `step4_notion_upload.py`
   - Notion API로 페이지 생성/업데이트
   - 수집된 메타데이터 업로드

### **설정 관리**
- **config.py**: 환경변수 로드 및 설정 값 관리
- **.env 파일**: API 키 및 민감한 정보 저장
- **상대/절대 경로 혼재**: config는 상대경로, batch_processor는 절대경로

## ⚠️ 리팩토링 시 고려사항

### **현재 시스템의 문제점**
1. **Import 경로 일관성 부족**: 절대경로와 상대경로 혼재
2. **PYTHONPATH 의존성**: 실행시 환경 설정 필요
3. **모듈 구조 복잡성**: tools/ 하위에 실행 파일 위치
4. **의존성 분산**: 각 step이 개별적으로 외부 라이브러리 호출

### **리팩토링 목표**
1. **통합 실행 방법**: PYTHONPATH 설정 없이 실행 가능
2. **일관된 Import**: 절대경로 또는 상대경로로 통일
3. **모듈 구조 단순화**: 공통 로직 추출 및 재사용
4. **의존성 중앙화**: 래퍼 클래스를 통한 외부 API 접근

## 📈 성능 기준점

### **현재 성능 (Phase 0 베이스라인)**
- **처리 속도**: 3개 애니메이션 29초 (평균 9.7초/개)
- **성공률**: 100% (3/3)
- **메모리 사용량**: 미측정
- **API 호출 수**: 
  - 라프텔 API: 6회 (검색 3회 + 메타데이터 3회)
  - OpenAI API: 3회 (매칭)
  - Notion API: 3회 (업로드)

---

**이 분석 결과는 Phase 2-4 리팩토링의 기반 자료로 활용됩니다.**
