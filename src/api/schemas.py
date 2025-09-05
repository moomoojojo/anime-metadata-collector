# 🎯 API 요청/응답 스키마 정의
"""
FastAPI용 API 스키마 정의
- 아이폰 단축어와의 통신 인터페이스
- 입력 검증 및 응답 형식 표준화
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

# core.models에서 기본 모델들 재사용
from ..core.models import ProcessStatus

# === API 요청 스키마 ===

class AnimeProcessRequest(BaseModel):
    """애니메이션 처리 요청"""
    title: str = Field(
        ..., 
        description="처리할 애니메이션 제목",
        min_length=1,
        max_length=200,
        example="스파이 패밀리"
    )
    description: Optional[str] = Field(
        None,
        description="요청 설명 (선택사항)",
        max_length=500,
        example="아이폰 단축어에서 요청"
    )
    user_id: Optional[str] = Field(
        None,
        description="사용자 식별자 (선택사항)",
        max_length=100
    )

class HealthCheckRequest(BaseModel):
    """헬스체크 요청 (선택적 상세 정보)"""
    detailed: Optional[bool] = Field(
        False,
        description="상세 헬스체크 여부"
    )

# === API 응답 스키마 ===

class AnimeProcessResponse(BaseModel):
    """애니메이션 처리 응답"""
    status: ProcessStatus = Field(..., description="처리 상태")
    anime_title: str = Field(..., description="요청된 애니메이션 제목")
    
    # 성공시 정보
    matched_title: Optional[str] = Field(None, description="매칭된 라프텔 제목")
    notion_page_url: Optional[str] = Field(None, description="생성된 노션 페이지 URL")
    processing_time: Optional[float] = Field(None, description="처리 시간(초)")
    steps_completed: int = Field(0, description="완료된 단계 수")
    
    # 실패시 정보
    error_message: Optional[str] = Field(None, description="오류 메시지")
    
    # 상세 정보 (선택적)
    metadata: Optional[Dict[str, Any]] = Field(None, description="수집된 메타데이터")
    
    # 메타 정보
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class HealthCheckResponse(BaseModel):
    """헬스체크 응답"""
    status: str = Field("healthy", description="시스템 상태")
    timestamp: datetime = Field(default_factory=datetime.now, description="확인 시간")
    version: str = Field("1.0.0", description="API 버전")
    environment: str = Field(..., description="실행 환경")
    
    # 상세 정보 (detailed=true일 때만)
    services: Optional[Dict[str, str]] = Field(None, description="서비스별 상태")
    system_info: Optional[Dict[str, Any]] = Field(None, description="시스템 정보")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# === 에러 응답 스키마 ===

class ErrorResponse(BaseModel):
    """API 에러 응답"""
    error: bool = Field(True, description="에러 여부")
    message: str = Field(..., description="에러 메시지")
    timestamp: float = Field(..., description="에러 발생 시간 (Unix timestamp)")
    path: Optional[str] = Field(None, description="요청 경로")
    details: Optional[Dict[str, Any]] = Field(None, description="에러 상세 정보")

# === 상태 조회 스키마 ===

class StatusResponse(BaseModel):
    """시스템 상태 조회 응답"""
    server_status: str = Field(..., description="서버 상태")
    environment: str = Field(..., description="실행 환경") 
    uptime_seconds: Optional[float] = Field(None, description="서버 가동 시간")
    active_connections: Optional[int] = Field(None, description="활성 연결 수")
    last_request_time: Optional[datetime] = Field(None, description="마지막 요청 시간")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# === 배치 호환성 스키마 (향후 API 통합용) ===

class BatchStatusRequest(BaseModel):
    """배치 상태 조회 요청"""
    batch_id: Optional[str] = Field(None, description="특정 배치 ID")
    
class BatchStatusResponse(BaseModel):
    """배치 상태 조회 응답"""
    batch_id: str = Field(..., description="배치 ID")
    status: ProcessStatus = Field(..., description="배치 상태")
    total_items: int = Field(..., description="총 처리 대상")
    completed_items: int = Field(..., description="완료된 항목")
    failed_items: int = Field(..., description="실패한 항목")
    success_rate: float = Field(..., description="성공률 (%)")
    start_time: datetime = Field(..., description="시작 시간")
    last_update: datetime = Field(..., description="마지막 업데이트")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# === 응답 예시들 (FastAPI 문서화용) ===

# 성공 응답 예시
SUCCESS_EXAMPLE = {
    "status": "success",
    "anime_title": "스파이 패밀리",
    "matched_title": "(자막) SPY×FAMILY part 1",
    "notion_page_url": "https://www.notion.so/spy-family-123456789",
    "processing_time": 25.6,
    "steps_completed": 4,
    "metadata": {
        "laftel_id": "40815",
        "name": "(자막) SPY×FAMILY part 1",
        "air_year_quarter": "2022년 2분기",
        "avg_rating": 4.8,
        "status": "완결",
        "production": "WIT STUDIO",
        "total_episodes": 12
    },
    "timestamp": "2024-09-05T15:30:45.123Z"
}

# 실패 응답 예시
FAILURE_EXAMPLE = {
    "status": "failed",
    "anime_title": "존재하지않는애니메이션",
    "error_message": "Step 1 실패: 검색 결과가 없습니다.",
    "steps_completed": 0,
    "timestamp": "2024-09-05T15:30:45.123Z"
}

# 부분 성공 예시 (검색 실패, 빈 페이지 생성)
PARTIAL_SUCCESS_EXAMPLE = {
    "status": "partial_success", 
    "anime_title": "모호한제목",
    "notion_page_url": "https://www.notion.so/empty-page-789",
    "processing_time": 8.2,
    "steps_completed": 1,
    "error_message": "검색 결과가 없어 빈 페이지만 생성됨",
    "timestamp": "2024-09-05T15:30:45.123Z"
}
