# 🎯 API용 애니메이션 처리기
"""
API 서버 전용 애니메이션 처리기
- AnimePipeline을 래핑하여 API 환경에 최적화
- 로깅, 에러 처리, 응답 변환 등 API 특화 기능
"""

import asyncio
import structlog
import time
from typing import Dict, Any, Optional
from datetime import datetime

from ..core.pipeline import AnimePipeline  
from ..core.models import ProcessResult, ProcessStatus, create_error_result
from ..core.config import settings
from .schemas import AnimeProcessResponse

logger = structlog.get_logger()

class ApiAnimeProcessor:
    """API 서버용 애니메이션 처리기"""
    
    def __init__(self):
        """프로세서 초기화"""
        self.pipeline = AnimePipeline()
        
    async def process(self, title: str) -> ProcessResult:
        """
        애니메이션 처리 (API 환경 최적화)
        
        Args:
            title: 처리할 애니메이션 제목
            
        Returns:
            ProcessResult: 처리 결과
        """
        request_id = f"api_{int(time.time())}"
        
        logger.info("API 애니메이션 처리 시작",
                   title=title,
                   request_id=request_id,
                   environment=settings.environment)
        
        start_time = time.time()
        
        try:
            # 입력 검증
            if not title or not title.strip():
                return create_error_result(
                    title="",
                    error_message="애니메이션 제목이 비어있습니다.",
                    steps_completed=0
                )
            
            title = title.strip()
            
            # 콜드 스타트 대응 (Render 무료 플랜)
            if settings.is_production:
                logger.info("프로덕션 환경 감지 - 콜드 스타트 최적화 적용")
                await self._warmup_services()
            
            # 파이프라인 실행 (현재는 동기 방식)
            logger.info("파이프라인 실행 시작", title=title)
            
            # 동기 호출 (현재 모든 클라이언트가 동기식)
            # TODO: 향후 실제 비동기 구현시 개선
            result = self._process_sync(title)
            
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            
            # 결과별 로깅
            if result.success:
                logger.info("API 애니메이션 처리 성공",
                           title=title,
                           matched_title=_extract_matched_title(result),
                           notion_url=result.notion_url,
                           processing_time=processing_time,
                           steps_completed=result.steps_completed,
                           request_id=request_id)
            else:
                logger.warning("API 애니메이션 처리 실패",
                              title=title,
                              error=result.error,
                              processing_time=processing_time,
                              steps_completed=result.steps_completed,
                              request_id=request_id)
            
            return result
            
        except asyncio.TimeoutError:
            error_msg = "처리 시간이 너무 오래 걸려 중단됨 (60초 초과)"
            logger.error("API 처리 타임아웃", 
                        title=title,
                        request_id=request_id)
            
            return create_error_result(title, error_msg, 0)
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"API 처리 중 예상치 못한 오류: {str(e)}"
            
            logger.error("API 처리 예외 발생",
                        title=title,
                        error=error_msg,
                        processing_time=processing_time,
                        request_id=request_id)
            
            result = create_error_result(title, error_msg, 0)
            result.processing_time = processing_time
            return result
    
    def process_sync(self, title: str) -> ProcessResult:
        """
        동기 방식 애니메이션 처리 (API 전용)
        
        Args:
            title: 처리할 애니메이션 제목
            
        Returns:
            ProcessResult: 처리 결과
        """
        request_id = f"api_{int(time.time())}"
        
        logger.info("API 애니메이션 처리 시작 (동기)",
                   title=title,
                   request_id=request_id,
                   environment=settings.environment)
        
        start_time = time.time()
        
        try:
            # 입력 검증
            if not title or not title.strip():
                return create_error_result(
                    title="",
                    error_message="애니메이션 제목이 비어있습니다.",
                    steps_completed=0
                )
            
            title = title.strip()
            
            # 파이프라인 실행 (동기 방식)
            logger.info("파이프라인 실행 시작", title=title)
            
            # 기존 배치와 동일한 방식으로 처리
            result = self.pipeline.process_single_sync(title)
            
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            
            # 결과별 로깅
            if result.success:
                logger.info("API 애니메이션 처리 성공",
                           title=title,
                           matched_title=_extract_matched_title(result),
                           notion_url=result.notion_url,
                           processing_time=processing_time,
                           steps_completed=result.steps_completed,
                           request_id=request_id)
            else:
                logger.warning("API 애니메이션 처리 실패",
                              title=title,
                              error=result.error,
                              processing_time=processing_time,
                              steps_completed=result.steps_completed,
                              request_id=request_id)
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"API 처리 중 예상치 못한 오류: {str(e)}"
            
            logger.error("API 처리 예외 발생",
                        title=title,
                        error=error_msg,
                        processing_time=processing_time,
                        request_id=request_id)
            
            result = create_error_result(title, error_msg, 0)
            result.processing_time = processing_time
            return result
    
    def _process_sync(self, title: str) -> ProcessResult:
        """동기 방식 애니메이션 처리"""
        try:
            # Step 1: 라프텔 검색
            search_result = self.pipeline.laftel.search_anime(title)
            
            if not search_result.success:
                return create_error_result(
                    title, f"Step 1 실패: {search_result.error_message}", 0
                )
            
            if not search_result.candidates:
                # 검색 실패시 빈 노션 페이지 생성
                notion_result = self.pipeline.notion.create_or_update_page(title, None)
                
                result = ProcessResult(
                    title=title,
                    success=notion_result.success,
                    status=ProcessStatus.PARTIAL_SUCCESS if notion_result.success else ProcessStatus.FAILED,
                    notion_url=notion_result.page_url if notion_result.success else None,
                    error="검색 결과가 없어 빈 페이지만 생성됨",
                    steps_completed=1 if notion_result.success else 0
                )
                
                return result
            
            # Step 2: AI 매칭
            llm_result = self.pipeline.openai.find_best_match(title, search_result.candidates)
            
            if not llm_result.success or not llm_result.selected_title:
                # 첫 번째 후보로 폴백
                if search_result.candidates:
                    llm_result.selected_title = search_result.candidates[0].title
                    llm_result.success = True
                else:
                    notion_result = self.pipeline.notion.create_or_update_page(title, None)
                    return create_error_result(title, f"Step 2 실패: {llm_result.error_message}", 1)
            
            # Step 3: 메타데이터 수집
            metadata_result = self.pipeline.laftel.get_metadata(llm_result.selected_title)
            
            # Step 4: 노션 업로드
            metadata_obj = metadata_result.metadata if metadata_result.success else None
            notion_result = self.pipeline.notion.create_or_update_page(title, metadata_obj)
            
            if not notion_result.success:
                return create_error_result(title, f"Step 4 실패: {notion_result.error_message}", 3)
            
            # 성공 결과 반환
            return ProcessResult(
                title=title,
                success=True,
                status=ProcessStatus.SUCCESS,
                notion_url=notion_result.page_url,
                steps_completed=4
            )
            
        except Exception as e:
            return create_error_result(title, f"처리 중 오류: {str(e)}", 0)

    async def _warmup_services(self):
        """서비스 워밍업 (콜드 스타트 최적화)"""
        try:
            # 설정 로드 확인
            _ = settings.openai_api_key
            
            # 파이프라인 헬스체크
            health = self.pipeline.health_check()
            
            logger.info("서비스 워밍업 완료", health_status=health.get("pipeline"))
            
        except Exception as e:
            logger.warning("서비스 워밍업 실패", error=str(e))
    
    def health_check(self) -> Dict[str, Any]:
        """프로세서 상태 확인"""
        try:
            pipeline_health = self.pipeline.health_check()
            
            return {
                "processor": "healthy",
                "pipeline": pipeline_health,
                "timestamp": datetime.now().isoformat(),
                "environment": settings.environment
            }
            
        except Exception as e:
            return {
                "processor": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

def _extract_matched_title(result: ProcessResult) -> Optional[str]:
    """처리 결과에서 매칭된 제목 추출"""
    if result.llm_result and result.llm_result.selected_title:
        return result.llm_result.selected_title
    elif result.metadata_result and result.metadata_result.metadata:
        return result.metadata_result.metadata.name
    else:
        return None

# === 응답 변환 헬퍼들 ===

class ResponseConverter:
    """ProcessResult를 API 응답으로 변환하는 헬퍼"""
    
    @staticmethod
    def to_api_response(result: ProcessResult, 
                       original_title: str) -> AnimeProcessResponse:
        """ProcessResult를 AnimeProcessResponse로 변환"""
        
        if result.success:
            return AnimeProcessResponse(
                status=ProcessStatus.SUCCESS,
                anime_title=original_title,
                matched_title=_extract_matched_title(result),
                notion_page_url=result.notion_url,
                processing_time=result.processing_time,
                steps_completed=result.steps_completed,
                metadata=_extract_metadata_dict(result)
            )
            
        elif result.status == ProcessStatus.PARTIAL_SUCCESS:
            return AnimeProcessResponse(
                status=ProcessStatus.PARTIAL_SUCCESS,
                anime_title=original_title,
                notion_page_url=result.notion_url,
                processing_time=result.processing_time,
                steps_completed=result.steps_completed,
                error_message=result.error
            )
            
        else:
            return AnimeProcessResponse(
                status=ProcessStatus.FAILED,
                anime_title=original_title,
                error_message=result.error,
                steps_completed=result.steps_completed,
                processing_time=result.processing_time
            )

def _extract_metadata_dict(result: ProcessResult) -> Optional[Dict[str, Any]]:
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
