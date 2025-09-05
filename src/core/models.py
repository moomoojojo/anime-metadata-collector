# 🎯 통합 데이터 모델 정의
"""
애니메이션 메타데이터 시스템용 공통 데이터 모델
- API 서버와 배치 처리 모두에서 사용
- Pydantic 기반으로 데이터 검증 및 직렬화 지원
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class ProcessStatus(str, Enum):
    """처리 상태 열거형"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"

class StepResult(BaseModel):
    """개별 단계 결과"""
    step_name: str
    success: bool
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

# === API 요청/응답 모델 ===

class AnimeRequest(BaseModel):
    """애니메이션 처리 요청"""
    title: str = Field(..., description="애니메이션 제목", min_length=1, max_length=200)
    user_id: Optional[str] = Field(None, description="사용자 ID")
    description: Optional[str] = Field(None, description="요청 설명")

class AnimeResponse(BaseModel):
    """애니메이션 처리 응답"""
    status: ProcessStatus
    anime_title: str
    matched_title: Optional[str] = None
    notion_page_url: Optional[str] = None
    processing_time: Optional[float] = None
    steps_completed: int = 0
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# === 단계별 결과 모델 ===

class SearchCandidate(BaseModel):
    """검색 후보 애니메이션"""
    title: str
    laftel_id: Optional[str] = None
    rank: int
    similarity_score: Optional[float] = None

class SearchResult(BaseModel):
    """Step 1: 라프텔 검색 결과"""
    user_input: str
    search_query: str
    candidates: List[SearchCandidate]
    total_found: int
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class LLMMatchResult(BaseModel):
    """Step 2: LLM 매칭 결과"""
    user_input: str
    candidates_count: int
    selected_title: Optional[str] = None
    confidence_score: Optional[float] = None
    reasoning: Optional[str] = None
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class AnimeMetadata(BaseModel):
    """애니메이션 메타데이터"""
    laftel_id: str
    name: str
    air_year_quarter: Optional[str] = None
    avg_rating: Optional[float] = None
    status: Optional[str] = None
    laftel_url: Optional[str] = None
    cover_url: Optional[str] = None
    production: Optional[str] = None
    total_episodes: Optional[int] = None
    genres: Optional[List[str]] = None
    description: Optional[str] = None

class MetadataResult(BaseModel):
    """Step 3: 메타데이터 수집 결과"""
    selected_title: str
    metadata: Optional[AnimeMetadata] = None
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class NotionResult(BaseModel):
    """Step 4: 노션 업로드 결과"""
    page_id: Optional[str] = None
    page_url: Optional[str] = None
    is_new_page: bool = False
    updated_properties: Optional[Dict[str, Any]] = None
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# === 통합 처리 결과 모델 ===

class ProcessResult(BaseModel):
    """전체 파이프라인 처리 결과"""
    title: str
    success: bool
    status: ProcessStatus
    notion_url: Optional[str] = None
    error: Optional[str] = None
    
    # 단계별 결과
    search_result: Optional[SearchResult] = None
    llm_result: Optional[LLMMatchResult] = None
    metadata_result: Optional[MetadataResult] = None
    notion_result: Optional[NotionResult] = None
    
    # 메타 정보
    processing_time: Optional[float] = None
    steps_completed: int = 0
    step_results: List[StepResult] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def add_step_result(self, step_name: str, success: bool, 
                       duration: Optional[float] = None, 
                       error: Optional[str] = None,
                       data: Optional[Dict[str, Any]] = None) -> None:
        """단계 결과 추가"""
        step_result = StepResult(
            step_name=step_name,
            success=success,
            duration_seconds=duration,
            error_message=error,
            data=data
        )
        self.step_results.append(step_result)
        if success:
            self.steps_completed += 1

# === 배치 처리용 모델 ===

class BatchConfig(BaseModel):
    """배치 처리 설정"""
    batch_id: str
    source_csv: str
    description: str
    notion_database_id: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.now)

class BatchSummary(BaseModel):
    """배치 처리 요약"""
    batch_id: str
    execution_summary: Dict[str, Any]
    step_statistics: Dict[str, int]
    failed_items: List[str]
    processing_details: List[Dict[str, Any]]
    execution_time: datetime = Field(default_factory=datetime.now)

# === 헬스체크 모델 ===

class HealthCheck(BaseModel):
    """시스템 상태 확인"""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    version: Optional[str] = None
    environment: Optional[str] = None
    services: Optional[Dict[str, str]] = None

# === 유틸리티 함수 ===

def create_error_result(title: str, error_message: str, 
                       steps_completed: int = 0) -> ProcessResult:
    """에러 결과 생성 헬퍼"""
    return ProcessResult(
        title=title,
        success=False,
        status=ProcessStatus.FAILED,
        error=error_message,
        steps_completed=steps_completed
    )

def create_success_result(title: str, notion_url: str,
                         processing_time: float = None) -> ProcessResult:
    """성공 결과 생성 헬퍼"""
    return ProcessResult(
        title=title,
        success=True,
        status=ProcessStatus.SUCCESS,
        notion_url=notion_url,
        processing_time=processing_time,
        steps_completed=4
    )
