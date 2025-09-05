# 🎯 통합 애니메이션 처리 파이프라인
"""
애니메이션 메타데이터 자동 수집 및 노션 업로드 통합 파이프라인
- 4단계 처리 과정을 하나의 클래스로 통합
- 배치 처리와 API 서버 모두에서 사용 가능
- 상세한 로깅 및 에러 처리 포함
"""

import time
from typing import Optional, Dict, Any
from datetime import datetime

from .models import (
    ProcessResult, ProcessStatus, SearchResult, 
    LLMMatchResult, MetadataResult, NotionResult,
    create_error_result, create_success_result
)
from .laftel_client import LaftelClient
from .openai_client import OpenAIClient
from .notion_client import NotionClient
from .config import settings

class AnimePipeline:
    """통합 애니메이션 처리 파이프라인"""
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        """
        파이프라인 초기화
        
        Args:
            config_override: 설정 오버라이드 (테스트용)
        """
        self.laftel = LaftelClient()
        self.openai = OpenAIClient()
        self.notion = NotionClient()
        
        # 설정 오버라이드 적용 (주로 테스트에서 사용)
        if config_override:
            # TODO: 필요시 설정 오버라이드 로직 구현
            pass
    
    async def process_single(self, title: str) -> ProcessResult:
        """
        단일 애니메이션 처리 (배치/API 공통 로직)
        
        Args:
            title: 처리할 애니메이션 제목
            
        Returns:
            ProcessResult: 처리 결과
        """
        start_time = time.time()
        
        print(f"\n{'='*80}")
        print(f"🎯 애니메이션 처리 시작: {title}")
        print(f"{'='*80}")
        
        try:
            # Step 1: 라프텔 검색
            print(f"\n🔍 Step 1: 검색 후보 수집")
            step1_start = time.time()
            
            search_result = self.laftel.search_anime(title)
            step1_duration = time.time() - step1_start
            
            if not search_result.success:
                return self._create_failure_result(
                    title, "Step 1 실패", search_result.error_message, 0,
                    search_result=search_result
                )
            
            if not search_result.candidates:
                # 검색 실패시 빈 노션 페이지만 생성
                print("⚠️ 검색 결과 없음 - 빈 노션 페이지 생성")
                notion_result = self.notion.create_or_update_page(title, None)
                
                result = ProcessResult(
                    title=title,
                    success=notion_result.success,
                    status=ProcessStatus.PARTIAL_SUCCESS if notion_result.success else ProcessStatus.FAILED,
                    notion_url=notion_result.page_url if notion_result.success else None,
                    error="검색 결과가 없어 빈 페이지만 생성됨",
                    search_result=search_result,
                    notion_result=notion_result,
                    processing_time=time.time() - start_time,
                    steps_completed=1 if notion_result.success else 0
                )
                
                result.add_step_result("search", True, step1_duration)
                if notion_result.success:
                    result.add_step_result("notion_fallback", True)
                    print("✅ 빈 노션 페이지 생성 완료")
                
                return result
            
            print(f"✅ 1단계 완료: {len(search_result.candidates)}개 후보 수집 성공")
            
            # Step 2: AI 매칭
            print(f"\n🤖 Step 2: LLM 매칭")
            step2_start = time.time()
            
            llm_result = self.openai.find_best_match(title, search_result.candidates)
            step2_duration = time.time() - step2_start
            
            if not llm_result.success or not llm_result.selected_title:
                # AI 매칭 실패시 첫 번째 후보 선택 또는 빈 페이지
                if search_result.candidates:
                    selected_title = search_result.candidates[0].title
                    print(f"⚠️ AI 매칭 실패 - 첫 번째 후보 선택: {selected_title}")
                    
                    # Step 3로 계속 진행
                    llm_result.selected_title = selected_title
                    llm_result.success = True
                    llm_result.confidence_score = 50.0  # 낮은 신뢰도
                else:
                    # 완전 실패
                    notion_result = self.notion.create_or_update_page(title, None)
                    return self._create_failure_result(
                        title, "Step 2 실패", llm_result.error_message, 1,
                        search_result=search_result, llm_result=llm_result,
                        notion_result=notion_result
                    )
            
            print(f"✅ 2단계 완료: 매칭 성공")
            
            # Step 3: 메타데이터 수집
            print(f"\n📊 Step 3: 메타데이터 수집")
            step3_start = time.time()
            
            metadata_result = self.laftel.get_metadata(llm_result.selected_title)
            step3_duration = time.time() - step3_start
            
            if not metadata_result.success:
                print("⚠️ 메타데이터 수집 실패 - 기본 정보만으로 진행")
                # 메타데이터 없이도 노션 페이지 생성 시도
            else:
                print(f"✅ 3단계 완료: 메타데이터 수집 성공")
            
            # Step 4: 노션 업로드
            print(f"\n📝 Step 4: 노션 업로드")
            step4_start = time.time()
            
            metadata_obj = metadata_result.metadata if metadata_result.success else None
            notion_result = self.notion.create_or_update_page(title, metadata_obj)
            step4_duration = time.time() - step4_start
            
            if not notion_result.success:
                return self._create_failure_result(
                    title, "Step 4 실패", notion_result.error_message, 3,
                    search_result=search_result, 
                    llm_result=llm_result,
                    metadata_result=metadata_result,
                    notion_result=notion_result
                )
            
            print(f"✅ 4단계 완료: 노션 업로드 성공")
            
            # 최종 성공 결과 생성
            total_time = time.time() - start_time
            
            result = ProcessResult(
                title=title,
                success=True,
                status=ProcessStatus.SUCCESS,
                notion_url=notion_result.page_url,
                search_result=search_result,
                llm_result=llm_result,
                metadata_result=metadata_result,
                notion_result=notion_result,
                processing_time=total_time,
                steps_completed=4
            )
            
            # 단계별 결과 추가
            result.add_step_result("search", True, step1_duration)
            result.add_step_result("llm_matching", True, step2_duration)
            result.add_step_result("metadata_collection", metadata_result.success, step3_duration,
                                 error=metadata_result.error_message if not metadata_result.success else None)
            result.add_step_result("notion_upload", True, step4_duration)
            
            print(f"\n✅ 전체 처리 성공!")
            print(f"📄 노션 URL: {notion_result.page_url}")
            print(f"⏱️ 총 소요시간: {total_time:.2f}초")
            
            return result
            
        except Exception as e:
            error_msg = f"파이프라인 처리 중 예상치 못한 오류: {str(e)}"
            print(f"❌ {error_msg}")
            
            return create_error_result(title, error_msg, 0)
    
    def process_single_sync(self, title: str) -> ProcessResult:
        """
        동기 버전의 단일 애니메이션 처리 (현재 구현은 동기식)
        
        Args:
            title: 처리할 애니메이션 제목
            
        Returns:
            ProcessResult: 처리 결과
        """
        # 현재 모든 클라이언트가 동기식이므로 바로 호출
        # 향후 비동기 지원시 이 부분을 수정
        import asyncio
        return asyncio.run(self.process_single(title))
    
    def _create_failure_result(self, title: str, step_name: str, error_message: str, 
                              steps_completed: int, **step_results) -> ProcessResult:
        """실패 결과 생성 헬퍼"""
        result = ProcessResult(
            title=title,
            success=False,
            status=ProcessStatus.FAILED,
            error=f"{step_name}: {error_message}",
            steps_completed=steps_completed,
            processing_time=time.time()  # 대략적인 시간
        )
        
        # 단계별 결과 추가
        if 'search_result' in step_results:
            result.search_result = step_results['search_result']
        if 'llm_result' in step_results:
            result.llm_result = step_results['llm_result']
        if 'metadata_result' in step_results:
            result.metadata_result = step_results['metadata_result']
        if 'notion_result' in step_results:
            result.notion_result = step_results['notion_result']
        
        return result
    
    def health_check(self) -> Dict[str, Any]:
        """파이프라인 상태 확인"""
        status = {
            "pipeline": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {}
        }
        
        try:
            # 설정 확인
            if not settings.openai_api_key:
                status["services"]["openai"] = "error - API key missing"
            else:
                status["services"]["openai"] = "ready"
                
            if not settings.notion_token:
                status["services"]["notion"] = "error - token missing"
            else:
                status["services"]["notion"] = "ready"
                
            status["services"]["laftel"] = "ready"  # 라프텔은 별도 인증 불필요
            
        except Exception as e:
            status["pipeline"] = "error"
            status["error"] = str(e)
        
        return status
    
    def get_statistics(self) -> Dict[str, Any]:
        """파이프라인 통계 정보 반환"""
        return {
            "pipeline_version": "2.0",
            "supported_steps": ["search", "llm_matching", "metadata_collection", "notion_upload"],
            "max_search_candidates": settings.max_search_candidates,
            "openai_model": settings.openai_model,
            "environment": "production" if settings.is_production else "development"
        }
