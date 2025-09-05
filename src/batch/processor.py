# 🔄 새로운 배치 프로세서 (코어 모듈 기반)
"""
리팩토링된 배치 처리기
- AnimePipeline을 사용하여 통합 로직 활용
- 기존 배치 처리 기능 유지
- 에러 처리 및 결과 저장 개선
"""

import os
import csv
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..core.pipeline import AnimePipeline
from ..core.models import ProcessResult, ProcessStatus, BatchConfig, BatchSummary, create_error_result
from ..core.config import settings

class BatchProcessor:
    """새로운 배치 처리기 (코어 모듈 기반)"""
    
    def __init__(self, csv_file: str, description: str = "", notion_db_id: str = None):
        """
        배치 처리기 초기화
        
        Args:
            csv_file: 처리할 CSV 파일 경로
            description: 배치 설명
            notion_db_id: 노션 데이터베이스 ID (None이면 기본값 사용)
        """
        self.csv_file = csv_file
        self.description = description
        
        # 배치 ID 생성 (기존 형식 유지)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        csv_name = Path(csv_file).stem
        self.batch_id = f"{timestamp}_{csv_name}_batch"
        
        # 결과 폴더 생성
        self.batch_folder = os.path.join("productions", self.batch_id)
        os.makedirs(self.batch_folder, exist_ok=True)
        
        # 하위 폴더 생성 (기존 구조 유지)
        for subfolder in ['search_results', 'llm_results', 'metadata_results', 'notion_results']:
            os.makedirs(os.path.join(self.batch_folder, subfolder), exist_ok=True)
        
        # 파이프라인 초기화
        self.pipeline = AnimePipeline()
        
        # 설정 오버라이드 (노션 DB ID)
        if notion_db_id:
            # TODO: 설정 오버라이드 구현
            pass
        
        print(f"🚀 배치 처리 시작")
        print(f"📁 배치 ID: {self.batch_id}")
        print(f"📂 배치 폴더: {self.batch_folder}")
    
    def load_anime_list(self) -> List[str]:
        """CSV 파일에서 애니메이션 목록 로드"""
        anime_list = []
        
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                
                # 헤더 스킵
                header = next(reader, None)
                if header:
                    print(f"📄 CSV 헤더: {header}")
                
                # 애니메이션 제목들 로드
                for row in reader:
                    if row and row[0].strip():  # 빈 행 스킵
                        anime_list.append(row[0].strip())
                        
            print(f"📋 애니메이션 목록 로드 완료: {len(anime_list)}개")
            return anime_list
            
        except Exception as e:
            print(f"❌ CSV 파일 로드 실패: {e}")
            return []
    
    def save_batch_config(self, anime_list: List[str]) -> None:
        """배치 설정 저장"""
        config_data = {
            "batch_id": self.batch_id,
            "source_csv": self.csv_file,
            "description": self.description,
            "total_items": len(anime_list),
            "start_time": datetime.now().isoformat(),
            "notion_database_id": settings.notion_database_id
        }
        
        config_file = os.path.join(self.batch_folder, "batch_config.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
    
    def save_step_result(self, step_name: str, index: int, title: str, 
                        result_data: Dict[str, Any]) -> str:
        """단계별 결과 저장"""
        folder_map = {
            "search": "search_results",
            "llm": "llm_results", 
            "metadata": "metadata_results",
            "notion": "notion_results"
        }
        
        subfolder = folder_map.get(step_name, step_name)
        filename = f"{step_name}_{index:02d}_{title}.json"
        filepath = os.path.join(self.batch_folder, subfolder, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # datetime 객체 자동 문자열 변환
                json.dump(result_data, f, ensure_ascii=False, indent=2, default=str)
            return filepath
        except Exception as e:
            print(f"⚠️ 결과 저장 실패: {e}")
            return ""
    
    def run_batch(self) -> bool:
        """배치 처리 실행"""
        start_time = time.time()
        
        try:
            # 애니메이션 목록 로드
            anime_list = self.load_anime_list()
            if not anime_list:
                print("❌ 처리할 애니메이션이 없습니다.")
                return False
            
            # 배치 설정 저장
            self.save_batch_config(anime_list)
            
            # 실행 통계
            success_count = 0
            failed_count = 0
            processing_details = []
            
            print(f"✅ 환경 설정 완료")
            
            # 각 애니메이션 처리
            for index, anime_title in enumerate(anime_list, 1):
                print(f"\n{'='*80}")
                print(f"🎯 [{index}/{len(anime_list)}] 처리 중: {anime_title}")
                print(f"{'='*80}")
                
                item_start_time = time.time()
                
                try:
                    # 통합 파이프라인으로 처리 (동기 방식)
                    result = self._process_single_sync(anime_title)
                    
                    # 결과별 처리
                    if result.success:
                        print(f"✅ 전체 처리 성공!")
                        success_count += 1
                    else:
                        print(f"❌ 처리 실패: {result.error}")
                        failed_count += 1
                    
                    # 처리 상세 정보 저장
                    item_detail = {
                        "anime_title": anime_title,
                        "index": index,
                        "start_time": datetime.fromtimestamp(item_start_time).isoformat(),
                        "steps": self._extract_step_details(result, index, anime_title),
                        "final_status": "success" if result.success else "failed",
                        "end_time": datetime.now().isoformat()
                    }
                    
                    processing_details.append(item_detail)
                    
                    # 진행률 표시
                    progress = (index / len(anime_list)) * 100
                    print(f"📊 진행률: {progress:.1f}% ({index}/{len(anime_list)})")
                    
                except KeyboardInterrupt:
                    print(f"\n❌ 사용자에 의해 중단됨 (처리 완료: {index-1}/{len(anime_list)})")
                    break
                    
                except Exception as e:
                    print(f"❌ 예상치 못한 오류: {e}")
                    failed_count += 1
                    
                    # 실패 항목도 기록
                    item_detail = {
                        "anime_title": anime_title,
                        "index": index,
                        "start_time": datetime.fromtimestamp(item_start_time).isoformat(),
                        "steps": {},
                        "final_status": "failed",
                        "error": str(e),
                        "end_time": datetime.now().isoformat()
                    }
                    processing_details.append(item_detail)
                    continue
            
            # 배치 요약 저장
            total_time = time.time() - start_time
            
            summary = BatchSummary(
                batch_id=self.batch_id,
                execution_summary={
                    "total_items": len(anime_list),
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "success_rate": f"{(success_count / len(anime_list) * 100):.1f}%"
                },
                step_statistics={
                    "step1_success": success_count,  # 성공한 것은 모든 단계 통과
                    "step2_success": success_count,
                    "step3_success": success_count,
                    "step4_success": success_count
                },
                failed_items=[item["anime_title"] for item in processing_details if item["final_status"] == "failed"],
                processing_details=processing_details
            )
            
            summary_file = os.path.join(self.batch_folder, "batch_summary.json")
            with open(summary_file, 'w', encoding='utf-8') as f:
                # JSON 직렬화를 위한 변환
                summary_data = summary.dict()
                # datetime 객체를 문자열로 변환
                if 'execution_time' in summary_data:
                    if hasattr(summary_data['execution_time'], 'isoformat'):
                        summary_data['execution_time'] = summary_data['execution_time'].isoformat()
                
                json.dump(summary_data, f, ensure_ascii=False, indent=2, default=str)
            
            # 최종 결과 출력
            print(f"\n{'='*80}")
            print(f"📊 배치 처리 완료!")
            print(f"📁 결과 폴더: {self.batch_folder}")
            print(f"📈 성공률: {(success_count / len(anime_list) * 100):.1f}%")
            print(f"✅ 성공: {success_count}개")
            print(f"❌ 실패: {failed_count}개")
            print(f"💾 요약 파일: {summary_file}")
            
            import datetime as dt
            duration = str(dt.timedelta(seconds=int(total_time)))
            print(f"⏱️ 총 소요시간: {duration}")
            
            return True
            
        except Exception as e:
            print(f"❌ 배치 처리 실패: {e}")
            return False
    
    def _process_single_sync(self, title: str) -> ProcessResult:
        """단일 애니메이션 동기 처리 (파이프라인 호출 방식 개선)"""
        try:
            # 단계별 직접 호출 (비동기 문제 해결)
            
            # Step 1: 라프텔 검색
            print(f"\n🔍 Step 1: 검색 후보 수집")
            search_result = self.pipeline.laftel.search_anime(title)
            
            if not search_result.success or not search_result.candidates:
                # 빈 노션 페이지 생성
                notion_result = self.pipeline.notion.create_or_update_page(title, None)
                return ProcessResult(
                    title=title,
                    success=notion_result.success,
                    status=ProcessStatus.PARTIAL_SUCCESS if notion_result.success else ProcessStatus.FAILED,
                    notion_url=notion_result.page_url if notion_result.success else None,
                    error="검색 결과가 없어 빈 페이지만 생성됨",
                    steps_completed=1 if notion_result.success else 0
                )
            
            print(f"✅ 1단계 완료: {len(search_result.candidates)}개 후보 수집 성공")
            
            # Step 2: AI 매칭
            print(f"\n🤖 Step 2: LLM 매칭") 
            llm_result = self.pipeline.openai.find_best_match(title, search_result.candidates)
            
            if not llm_result.success or not llm_result.selected_title:
                # 첫 번째 후보로 폴백
                if search_result.candidates:
                    llm_result.selected_title = search_result.candidates[0].title
                    llm_result.success = True
                    print(f"⚠️ AI 매칭 실패 - 첫 번째 후보 선택: {llm_result.selected_title}")
                else:
                    return create_error_result(title, f"Step 2 실패: {llm_result.error_message}", 1)
            
            print(f"✅ 2단계 완료: 매칭 성공")
            
            # Step 3: 메타데이터 수집
            print(f"\n📊 Step 3: 메타데이터 수집")
            metadata_result = self.pipeline.laftel.get_metadata(llm_result.selected_title)
            
            if not metadata_result.success:
                print("⚠️ 메타데이터 수집 실패 - 기본 정보만으로 진행")
            else:
                print(f"✅ 3단계 완료: 메타데이터 수집 성공")
            
            # Step 4: 노션 업로드
            print(f"\n📝 Step 4: 노션 업로드")
            metadata_obj = metadata_result.metadata if metadata_result.success else None
            notion_result = self.pipeline.notion.create_or_update_page(title, metadata_obj)
            
            if not notion_result.success:
                return create_error_result(title, f"Step 4 실패: {notion_result.error_message}", 3)
            
            print(f"✅ 4단계 완료: 노션 업로드 성공")
            
            # 최종 성공 결과
            return ProcessResult(
                title=title,
                success=True,
                status=ProcessStatus.SUCCESS,
                notion_url=notion_result.page_url,
                search_result=search_result,
                llm_result=llm_result,
                metadata_result=metadata_result,
                notion_result=notion_result,
                steps_completed=4
            )
            
        except Exception as e:
            error_msg = f"단일 애니메이션 처리 실패: {str(e)}"
            print(f"❌ {error_msg}")
            return create_error_result(title, error_msg, 0)
    
    def _extract_step_details(self, result: ProcessResult, index: int, title: str) -> Dict[str, Any]:
        """단계별 결과 상세 정보 추출 및 파일 저장"""
        steps = {}
        
        # Step 1: 검색 결과
        if result.search_result:
            search_data = result.search_result.dict()
            search_file = self.save_step_result("search", index, title, search_data)
            steps["step1"] = {
                "success": result.search_result.success,
                "file": search_file,
                "candidates_count": len(result.search_result.candidates)
            }
        
        # Step 2: LLM 결과
        if result.llm_result:
            llm_data = result.llm_result.dict()
            llm_file = self.save_step_result("llm", index, title, llm_data)
            steps["step2"] = {
                "success": result.llm_result.success,
                "file": llm_file,
                "match_status": "match_found" if result.llm_result.selected_title else "no_match"
            }
        
        # Step 3: 메타데이터 결과
        if result.metadata_result:
            metadata_data = result.metadata_result.dict()
            metadata_file = self.save_step_result("metadata", index, title, metadata_data)
            steps["step3"] = {
                "success": result.metadata_result.success,
                "file": metadata_file
            }
        
        # Step 4: 노션 결과  
        if result.notion_result:
            notion_data = result.notion_result.dict()
            notion_file = self.save_step_result("notion", index, title, notion_data)
            steps["step4"] = {
                "success": result.notion_result.success,
                "file": notion_file,
                "notion_page_url": result.notion_result.page_url
            }
        
        return steps

# === 하위 호환성을 위한 레거시 래퍼 ===

def create_batch_processor(csv_file: str, description: str = "", notion_db_id: str = None):
    """기존 인터페이스 호환성을 위한 팩토리 함수"""
    return BatchProcessor(csv_file, description, notion_db_id)
