# LLM 기반 스마트 애니메이션 매칭 시스템 개발 계획

## 🎯 목표
사용자 입력 애니메이션 제목과 라프텔 검색 결과를 LLM이 분석하여 가장 적절한 작품을 자동 선택

## 📊 전체 플로우
```
입력 제목 → 라프텔 검색 → LLM 매칭 → 메타데이터 수집 → 노션 업로드
```

## 🔧 기술 스택
- **라프텔 API**: 검색 및 메타데이터 수집
- **LLM API**: OpenAI GPT-4 또는 Claude (매칭 판단)
- **노션 API**: 데이터베이스 입력

## 📋 개발 단계

### Phase 1: LLM 매칭 엔진 개발
- [ ] LLM API 연동 (OpenAI/Anthropic)
- [ ] 매칭 프롬프트 설계
- [ ] 후보작 분석 로직 구현
- [ ] 매칭 결과 검증 시스템

### Phase 2: 통합 시스템 구축
- [ ] 기존 라프텔 API와 통합
- [ ] 에러 처리 및 폴백 시스템
- [ ] 매칭 신뢰도 점수 시스템
- [ ] 사용자 확인 인터페이스

### Phase 3: 최적화 및 고도화
- [ ] 매칭 성능 개선
- [ ] 배치 처리 지원
- [ ] 매칭 히스토리 학습
- [ ] 사용자 피드백 시스템

## 🏗️ 아키텍처 설계

### 핵심 컴포넌트
1. **SearchEngine**: 라프텔 검색 및 후보 수집
2. **LLMMatchingEngine**: 후보 분석 및 최적 선택
3. **MetadataCollector**: 선택된 작품의 상세 정보 수집
4. **NotionUploader**: 노션 데이터베이스 입력

### 데이터 플로우
```python
# 1. 검색 및 후보 수집
candidates = search_engine.search(user_input)

# 2. LLM 매칭
best_match = llm_engine.find_best_match(user_input, candidates)

# 3. 메타데이터 수집
metadata = collector.collect(best_match.anime_id)

# 4. 노션 업로드
notion_uploader.create_page(metadata)
```

## 🎨 LLM 프롬프트 설계

### 매칭 프롬프트 구조
```
사용자가 찾는 애니메이션: "{user_input}"

검색 결과 후보들:
1. 제목: "{candidate.title}"
   방영분기: "{candidate.air_year_quarter}"
   장르: "{candidate.genres}"
   화수: "{candidate.total_episodes}"
   
2. ...

분석 기준:
- 제목 유사성
- 시즌/시리즈 일치성
- 방영 시기 적절성
- 장르 일치성

가장 적절한 후보를 선택하고 이유를 설명하세요.
```

## 🔍 매칭 알고리즘 설계

### 1. 기본 매칭 로직
```python
def analyze_candidates(user_input: str, candidates: List[Candidate]):
    prompt = create_matching_prompt(user_input, candidates)
    llm_response = llm_api.call(prompt)
    
    return {
        "selected_id": llm_response.selected_id,
        "confidence_score": llm_response.confidence,
        "reasoning": llm_response.reasoning
    }
```

### 2. 신뢰도 기반 처리
- **고신뢰도 (0.8+)**: 자동 진행
- **중신뢰도 (0.5-0.8)**: 사용자 확인 요청
- **저신뢰도 (0.5-)**: 수동 선택 또는 재검색

### 3. 폴백 시스템
- LLM 매칭 실패 시 기존 유사도 알고리즘 사용
- 네트워크 오류 시 캐시된 결과 활용

## 📊 데이터 구조

### Candidate 클래스
```python
@dataclass
class Candidate:
    anime_id: int
    title: str
    air_year_quarter: str
    genres: List[str]
    total_episodes: int
    avg_rating: float
    similarity_score: float  # 기존 알고리즘 점수
```

### MatchingResult 클래스
```python
@dataclass
class MatchingResult:
    selected_candidate: Candidate
    confidence_score: float
    reasoning: str
    llm_model: str
    timestamp: datetime
```

## 🧪 테스트 전략

### 1. 단위 테스트
- 각 컴포넌트별 독립 테스트
- 모킹을 통한 API 테스트

### 2. 통합 테스트
- 전체 플로우 테스트
- 실제 API 연동 테스트

### 3. 정확도 테스트
- 알려진 정답 데이터셋으로 매칭 정확도 측정
- 기존 방식과 성능 비교

## ⚠️ 고려사항

### 1. 비용 관리
- LLM API 호출 비용 최적화
- 캐싱을 통한 중복 호출 방지

### 2. 속도 최적화
- 비동기 처리로 응답 시간 단축
- 배치 처리 지원

### 3. 에러 처리
- LLM API 장애 시 폴백 시스템
- 부분 실패 시 복구 메커니즘

### 4. 확장성
- 다른 애니메이션 플랫폼 지원 준비
- 다양한 LLM 모델 지원

## 📈 성공 지표
- 매칭 정확도: 90% 이상
- 응답 시간: 10초 이내
- 사용자 만족도: 4.5/5.0 이상
- 비용 효율성: 건당 $0.01 이하
