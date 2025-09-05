# 🎬 애니메이션 처리 API 라우터
"""
메인 애니메이션 메타데이터 처리 API
- 아이폰 단축어의 핵심 엔드포인트
- 4단계 파이프라인 실행 및 결과 반환
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import time
import structlog
from datetime import datetime
from typing import Dict, Any

from ...core.pipeline import AnimePipeline
from ...core.models import ProcessStatus, ProcessResult
from ..schemas import (
    AnimeProcessRequest, AnimeProcessResponse, 
    SUCCESS_EXAMPLE, FAILURE_EXAMPLE, PARTIAL_SUCCESS_EXAMPLE
)
from ..processor import ApiAnimeProcessor

router = APIRouter(prefix="/api/v1", tags=["anime"])
logger = structlog.get_logger()

@router.post("/process-anime", 
            response_model=AnimeProcessResponse,
            summary="애니메이션 자동 처리",
            description="애니메이션 제목을 받아서 라프텔 검색 → AI 매칭 → 메타데이터 수집 → 노션 업로드를 자동 실행")
async def process_anime(request: AnimeProcessRequest):
    """
    개별 애니메이션 즉시 처리 (아이폰 단축어 전용)
    """
    start_time = time.time()
    
    logger.info("애니메이션 처리 요청 시작",
               title=request.title,
               user_id=request.user_id,
               description=request.description)
    
    try:
        # API 전용 프로세서 사용
        processor = ApiAnimeProcessor()
        
        # 4단계 파이프라인 실행
        result = await processor.process(request.title)
        
        processing_time = time.time() - start_time
        result.processing_time = processing_time
        
        # 로그 기록
        logger.info("애니메이션 처리 완료",
                   title=request.title,
                   success=result.success,
                   steps_completed=result.steps_completed,
                   processing_time=processing_time)
        
        # 응답 형태 변환
        if result.success:
            response = AnimeProcessResponse(
                status=ProcessStatus.SUCCESS,
                anime_title=request.title,
                matched_title=_extract_matched_title(result),
                notion_page_url=result.notion_url,
                processing_time=processing_time,
                steps_completed=result.steps_completed,
                metadata=_extract_metadata_dict(result)
            )
            
            logger.info("성공 응답 반환", notion_url=result.notion_url)
            
        elif result.status == ProcessStatus.PARTIAL_SUCCESS:
            response = AnimeProcessResponse(
                status=ProcessStatus.PARTIAL_SUCCESS,
                anime_title=request.title,
                notion_page_url=result.notion_url,
                processing_time=processing_time,
                steps_completed=result.steps_completed,
                error_message=result.error
            )
            
            logger.warning("부분 성공 응답", error=result.error)
            
        else:
            response = AnimeProcessResponse(
                status=ProcessStatus.FAILED,
                anime_title=request.title,
                error_message=result.error,
                steps_completed=result.steps_completed,
                processing_time=processing_time
            )
            
            logger.error("실패 응답", error=result.error)
        
        return response
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"처리 중 예상치 못한 오류: {str(e)}"
        
        logger.error("애니메이션 처리 예외 발생",
                    title=request.title,
                    error=error_msg,
                    processing_time=processing_time)
        
        raise HTTPException(
            status_code=500, 
            detail={
                "error": True,
                "message": error_msg,
                "anime_title": request.title,
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get("/status")
async def api_status():
    """API 서버 상태 확인"""
    try:
        # 파이프라인 상태 확인
        pipeline = AnimePipeline()
        health = pipeline.health_check()
        stats = pipeline.get_statistics()
        
        return {
            "api_status": "operational",
            "timestamp": datetime.now().isoformat(),
            "environment": settings.environment,
            "pipeline_health": health,
            "statistics": stats,
            "uptime_seconds": round(time.time() - SERVER_START_TIME, 2)
        }
        
    except Exception as e:
        logger.error("상태 확인 실패", error=str(e))
        raise HTTPException(status_code=500, detail=f"상태 확인 실패: {str(e)}")

@router.get("/test-connection")
async def test_external_connections():
    """외부 서비스 연결 테스트 (개발/디버깅용)"""
    if not settings.debug:
        raise HTTPException(status_code=404, detail="개발 모드에서만 사용 가능")
    
    try:
        pipeline = AnimePipeline()
        
        # 각 서비스별 기본 연결 테스트 (실제 API 호출은 하지 않음)
        test_results = {
            "openai": {
                "configured": bool(settings.openai_api_key),
                "key_format": settings.openai_api_key.startswith("sk-") if settings.openai_api_key else False
            },
            "notion": {
                "configured": bool(settings.notion_token),
                "token_format": settings.notion_token.startswith("secret_") if settings.notion_token else False
            },
            "laftel": {
                "configured": True,  # 별도 인증 불필요
                "library_imported": True
            },
            "pipeline": {
                "initialized": True
            }
        }
        
        return {
            "connection_tests": test_results,
            "timestamp": datetime.now().isoformat(),
            "note": "실제 API 호출은 하지 않고 설정만 확인함"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"연결 테스트 실패: {str(e)}")

def _extract_matched_title(result: ProcessResult) -> str:
    """처리 결과에서 매칭된 제목 추출"""
    if result.llm_result and result.llm_result.selected_title:
        return result.llm_result.selected_title
    elif result.metadata_result and result.metadata_result.metadata:
        return result.metadata_result.metadata.name
    else:
        return None

def _extract_metadata_dict(result: ProcessResult) -> Dict[str, Any]:
    """처리 결과에서 메타데이터 사전 추출"""
    if result.metadata_result and result.metadata_result.metadata:
        metadata = result.metadata_result.metadata
        return {
            "laftel_id": metadata.laftel_id,
            "name": metadata.name,
            "air_year_quarter": metadata.air_year_quarter,
            "avg_rating": metadata.avg_rating,
            "status": metadata.status,
            "laftel_url": metadata.laftel_url,
            "cover_url": metadata.cover_url,
            "production": metadata.production,
            "total_episodes": metadata.total_episodes
        }
    else:
        return None
