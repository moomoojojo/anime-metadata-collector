#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
배치 처리 스크립트 - 여러 애니메이션을 한 번에 처리

사용법:
    python tools/batch_processor.py --csv anime.csv --description "첫 번째 25개 애니메이션"
    python tools/batch_processor.py --csv anime.csv --db-id NEW_DB_ID --description "새 데이터베이스 테스트"
"""

import os
import sys
import csv
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any
import subprocess

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.anime_metadata import step1_search_candidates
from src.anime_metadata import step2_llm_matching
from src.anime_metadata import step3_metadata_collection
from src.anime_metadata import step4_notion_upload
from src.anime_metadata import config
import laftel

class BatchProcessor:
    def __init__(self, csv_file: str, description: str = "", notion_db_id: str = None):
        self.csv_file = csv_file
        self.description = description
        self.notion_db_id = notion_db_id
        
        # 배치 ID 생성 (날짜_시간_파일명)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        csv_name = os.path.splitext(os.path.basename(csv_file))[0]
        self.batch_id = f"{timestamp}_{csv_name}_batch"
        
        # 배치 폴더 경로
        self.batch_dir = os.path.join("productions", self.batch_id)
        
        # 결과 폴더들
        self.search_dir = os.path.join(self.batch_dir, "search_results")
        self.llm_dir = os.path.join(self.batch_dir, "llm_results")
        self.metadata_dir = os.path.join(self.batch_dir, "metadata_results")
        self.notion_dir = os.path.join(self.batch_dir, "notion_results")
        
        # 배치 상태
        self.anime_list = []
        self.results = {
            "success_count": 0,
            "failed_items": [],
            "step_stats": {
                "step1_success": 0,
                "step2_success": 0,
                "step3_success": 0,
                "step4_success": 0
            }
        }
    
    def setup_batch_environment(self):
        """배치 처리 환경 설정"""
        print(f"🚀 배치 처리 환경 설정")
        print(f"📁 배치 ID: {self.batch_id}")
        print(f"📂 배치 폴더: {self.batch_dir}")
        
        # 폴더 생성
        os.makedirs(self.batch_dir, exist_ok=True)
        os.makedirs(self.search_dir, exist_ok=True)
        os.makedirs(self.llm_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
        os.makedirs(self.notion_dir, exist_ok=True)
        
        # 임시로 환경변수 설정 (노션 DB ID가 지정된 경우)
        if self.notion_db_id:
            os.environ['NOTION_DATABASE_ID'] = self.notion_db_id
            print(f"🔧 노션 DB ID 임시 변경: {self.notion_db_id}")
        
        # 배치 설정 파일 생성
        config_data = {
            "batch_id": self.batch_id,
            "execution_date": datetime.now().isoformat(),
            "source_csv": self.csv_file,
            "description": self.description,
            "notion_database_id": self.notion_db_id or os.getenv('NOTION_DATABASE_ID'),
            "openai_model": "gpt-4",
            "total_items": 0  # 나중에 업데이트
        }
        
        config_file = os.path.join(self.batch_dir, "batch_config.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 환경 설정 완료")
    
    def collect_metadata_for_batch(self, llm_result: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """배치 처리용 메타데이터 수집 함수 (개별 LLM 결과 사용)"""
        try:
            # 매칭 상태 확인
            match_status = llm_result.get("match_status")
            if match_status != "match_found":
                print(f"⏭️ 3단계 건너뛰기: 2단계에서 매칭되지 않음")
                print(f"   매칭 상태: {match_status}")
                print(f"   이유: {llm_result.get('reason', '알 수 없음')}")
                
                return {
                    "metadata_success": False,
                    "skip_reason": "2단계에서 매칭되지 않음",
                    "llm_status": match_status,
                    "llm_reason": llm_result.get("reason", ""),
                    "user_input": user_input,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 매칭 성공한 경우 메타데이터 수집
            selected_title = llm_result["selected_title"]
            confidence = llm_result.get("confidence", 0)
            
            print(f"✅ 2단계 매칭 성공 확인")
            print(f"   원본 입력: {user_input}")
            print(f"   선택된 제목: {selected_title}")
            print(f"   신뢰도: {confidence}%")
            
            # 애니메이션 ID 찾기
            anime_id = self.find_anime_id_by_title(selected_title, user_input)
            if not anime_id:
                return {
                    "metadata_success": False,
                    "error": "애니메이션 ID를 찾을 수 없음",
                    "selected_title": selected_title,
                    "user_input": user_input,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 상세 메타데이터 수집
            metadata = self.fetch_detailed_metadata(anime_id)
            if not metadata:
                return {
                    "metadata_success": False,
                    "error": "메타데이터 수집 실패",
                    "anime_id": anime_id,
                    "selected_title": selected_title,
                    "user_input": user_input,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 결과 구성
            result = {
                "metadata_success": True,
                "user_input": user_input,
                "selected_title": selected_title,
                "anime_id": anime_id,
                "confidence": confidence,
                "metadata": metadata,
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            print(f"❌ 메타데이터 수집 중 오류: {e}")
            return {
                "metadata_success": False,
                "error": str(e),
                "user_input": user_input,
                "timestamp": datetime.now().isoformat()
            }
    
    def find_anime_id_by_title(self, selected_title: str, user_input: str) -> int:
        """선택된 제목으로 애니메이션 ID 찾기"""
        try:
            print(f"🔍 애니메이션 ID 검색 중...")
            print(f"   선택된 제목: {selected_title}")
            
            # 선택된 제목으로 다시 검색해서 정확한 ID 찾기
            search_results = laftel.sync.searchAnime(selected_title)
            
            if not search_results:
                print(f"❌ '{selected_title}'로 검색 결과가 없습니다.")
                return None
            
            # 정확히 일치하는 제목 찾기
            for result in search_results:
                if result.name == selected_title:
                    print(f"✅ 정확한 매칭 발견: ID {result.id}")
                    return result.id
            
            # 정확한 매칭이 없으면 첫 번째 결과 사용
            first_result = search_results[0]
            print(f"⚠️ 정확한 매칭 없음, 첫 번째 결과 사용: ID {first_result.id}")
            print(f"   첫 번째 결과: {first_result.name}")
            
            return first_result.id
            
        except Exception as e:
            print(f"❌ ID 검색 중 오류: {e}")
            return None
    
    def fetch_detailed_metadata(self, anime_id: int) -> Dict[str, Any]:
        """애니메이션 ID로 상세 메타데이터 수집"""
        try:
            print(f"📊 상세 정보 수집 중... (ID: {anime_id})")
            
            # 애니메이션 상세 정보
            info = laftel.sync.getAnimeInfo(anime_id)
            print(f"✅ 기본 정보 수집 완료: {info.name}")
            
            # 에피소드 정보로 총 화수 계산
            print(f"🎬 에피소드 정보 조회 중...")
            try:
                episodes = laftel.sync.searchEpisodes(anime_id)
                total_episodes = len(episodes) if episodes else 0
                print(f"📺 총 {total_episodes}화 확인")
            except Exception as ep_error:
                print(f"⚠️ 에피소드 정보 조회 실패: {ep_error}")
                total_episodes = 0
            
            # 상태 판정
            status = "완결" if getattr(info, "ended", False) else "방영중"
            
            metadata = {
                "name": info.name or "",
                "air_year_quarter": info.air_year_quarter or "",
                "avg_rating": info.avg_rating or 0.0,
                "status": status,
                "laftel_url": info.url or "",
                "cover_url": info.image or "",
                "production": info.production.get("name", "") if isinstance(info.production, dict) else (info.production or ""),
                "total_episodes": total_episodes
            }
            
            print(f"✅ 메타데이터 수집 완료!")
            print(f"   제목: {metadata['name']}")
            print(f"   방영분기: {metadata['air_year_quarter']}")
            print(f"   평점: {metadata['avg_rating']}")
            print(f"   상태: {metadata['status']}")
            print(f"   제작사: {metadata['production']}")
            print(f"   총 화수: {metadata['total_episodes']}화")
            
            return metadata
            
        except Exception as e:
            print(f"❌ 메타데이터 수집 실패: {e}")
            return {}
    
    def load_anime_list(self):
        """CSV에서 애니메이션 목록 로드"""
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # 헤더 스킵
                self.anime_list = [row[0] for row in reader if row[0].strip()]
            
            print(f"📋 애니메이션 목록 로드 완료: {len(self.anime_list)}개")
            
            # 배치 설정 업데이트
            config_file = os.path.join(self.batch_dir, "batch_config.json")
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            config_data["total_items"] = len(self.anime_list)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"❌ CSV 로드 실패: {e}")
            return False
    
    def process_single_anime(self, anime_title: str, index: int) -> Dict[str, Any]:
        """단일 애니메이션 처리 (4단계 모두)"""
        print(f"\n{'='*80}")
        print(f"🎯 [{index+1}/{len(self.anime_list)}] 처리 중: {anime_title}")
        print(f"{'='*80}")
        
        result = {
            "anime_title": anime_title,
            "index": index + 1,
            "start_time": datetime.now().isoformat(),
            "steps": {}
        }
        
        try:
            # Step 1: 검색 후보 수집
            print(f"\n🔍 Step 1: 검색 후보 수집")
            search_result = step1_search_candidates.collect_search_candidates(anime_title)
            
            # 결과 저장
            search_file = os.path.join(self.search_dir, f"search_{index+1:02d}_{anime_title.replace('/', '_')}.json")
            with open(search_file, 'w', encoding='utf-8') as f:
                json.dump(search_result, f, ensure_ascii=False, indent=2)
            
            result["steps"]["step1"] = {
                "success": search_result.get("search_success", False),
                "file": search_file,
                "candidates_count": len(search_result.get("candidate_titles", []))
            }
            
            if not search_result.get("search_success"):
                print(f"❌ Step 1 실패: {search_result.get('error_message', '알 수 없는 오류')}")
                print(f"📝 라프텔에 없는 애니메이션도 노션 페이지 생성")
                
                # 라프텔에 없어도 노션 페이지는 생성
                notion_result = step4_notion_upload.upload_to_notion(None, anime_title)
                
                notion_file = os.path.join(self.notion_dir, f"notion_{index+1:02d}_{anime_title.replace('/', '_')}.json")
                notion_result["upload_timestamp"] = datetime.now().isoformat()
                notion_result["user_input"] = anime_title
                
                with open(notion_file, 'w', encoding='utf-8') as f:
                    json.dump(notion_result, f, ensure_ascii=False, indent=2)
                
                result["steps"]["step4"] = {
                    "success": notion_result.get("upload_success", False),
                    "file": notion_file,
                    "notion_page_url": notion_result.get("notion_page_url", "")
                }
                
                if notion_result.get("upload_success"):
                    self.results["step_stats"]["step4_success"] += 1
                    result["final_status"] = "step1_failed_but_notion_created"
                    print(f"✅ 노션 페이지 생성 성공 (라프텔 정보 없음)")
                else:
                    result["final_status"] = "step1_failed"
                
                return result
            
            self.results["step_stats"]["step1_success"] += 1
            
            # Step 2: LLM 매칭
            print(f"\n🤖 Step 2: LLM 매칭")
            llm_result = step2_llm_matching.perform_llm_matching(
                anime_title, 
                search_result["candidate_titles"]
            )
            
            # 결과 저장
            llm_file = os.path.join(self.llm_dir, f"llm_{index+1:02d}_{anime_title.replace('/', '_')}.json")
            with open(llm_file, 'w', encoding='utf-8') as f:
                json.dump(llm_result, f, ensure_ascii=False, indent=2)
            
            result["steps"]["step2"] = {
                "success": llm_result.get("matching_success", False),
                "file": llm_file,
                "match_status": llm_result.get("match_status", "unknown")
            }
            
            if not llm_result.get("matching_success") or llm_result.get("match_status") != "match_found":
                print(f"❌ Step 2 실패: 매칭되지 않음")
                print(f"📝 LLM 매칭 실패해도 노션 페이지 생성")
                
                # LLM 매칭 실패해도 노션 페이지는 생성
                notion_result = step4_notion_upload.upload_to_notion(None, anime_title)
                
                notion_file = os.path.join(self.notion_dir, f"notion_{index+1:02d}_{anime_title.replace('/', '_')}.json")
                notion_result["upload_timestamp"] = datetime.now().isoformat()
                notion_result["user_input"] = anime_title
                
                with open(notion_file, 'w', encoding='utf-8') as f:
                    json.dump(notion_result, f, ensure_ascii=False, indent=2)
                
                result["steps"]["step4"] = {
                    "success": notion_result.get("upload_success", False),
                    "file": notion_file,
                    "notion_page_url": notion_result.get("notion_page_url", "")
                }
                
                if notion_result.get("upload_success"):
                    self.results["step_stats"]["step4_success"] += 1
                    result["final_status"] = "step2_failed_but_notion_created"
                    print(f"✅ 노션 페이지 생성 성공 (LLM 매칭 실패)")
                else:
                    result["final_status"] = "step2_failed"
                
                return result
            
            self.results["step_stats"]["step2_success"] += 1
            
            # Step 3: 메타데이터 수집
            print(f"\n📊 Step 3: 메타데이터 수집")
            
            metadata_result = self.collect_metadata_for_batch(llm_result, anime_title)
            
            # 결과 저장
            metadata_file = os.path.join(self.metadata_dir, f"metadata_{index+1:02d}_{anime_title.replace('/', '_')}.json")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata_result, f, ensure_ascii=False, indent=2)
            
            result["steps"]["step3"] = {
                "success": metadata_result.get("metadata_success", False),
                "file": metadata_file
            }
            
            if not metadata_result.get("metadata_success"):
                print(f"❌ Step 3 실패: 메타데이터 수집 실패")
                result["final_status"] = "step3_failed"
                return result
            
            self.results["step_stats"]["step3_success"] += 1
            
            # Step 4: 노션 업로드
            print(f"\n📝 Step 4: 노션 업로드")
            
            notion_result = step4_notion_upload.upload_to_notion(
                metadata_result["metadata"], 
                anime_title
            )
            
            # 결과 저장
            notion_file = os.path.join(self.notion_dir, f"notion_{index+1:02d}_{anime_title.replace('/', '_')}.json")
            notion_result["upload_timestamp"] = datetime.now().isoformat()
            notion_result["user_input"] = anime_title
            
            with open(notion_file, 'w', encoding='utf-8') as f:
                json.dump(notion_result, f, ensure_ascii=False, indent=2)
            
            result["steps"]["step4"] = {
                "success": notion_result.get("upload_success", False),
                "file": notion_file,
                "notion_page_url": notion_result.get("notion_page_url", "")
            }
            
            if not notion_result.get("upload_success"):
                print(f"❌ Step 4 실패: 노션 업로드 실패")
                result["final_status"] = "step4_failed"
                return result
            
            self.results["step_stats"]["step4_success"] += 1
            
            # 전체 성공
            result["final_status"] = "success"
            self.results["success_count"] += 1
            print(f"✅ 전체 처리 성공!")
            
        except Exception as e:
            print(f"❌ 처리 중 오류 발생: {e}")
            result["final_status"] = "error"
            result["error"] = str(e)
            self.results["failed_items"].append({
                "title": anime_title,
                "reason": str(e)
            })
        
        finally:
            result["end_time"] = datetime.now().isoformat()
        
        return result
    
    def save_batch_summary(self, processing_results: List[Dict[str, Any]]):
        """배치 처리 요약 저장"""
        summary = {
            "batch_id": self.batch_id,
            "execution_summary": {
                "total_items": len(self.anime_list),
                "success_count": self.results["success_count"],
                "failed_count": len(self.anime_list) - self.results["success_count"],
                "success_rate": f"{(self.results['success_count'] / len(self.anime_list)) * 100:.1f}%"
            },
            "step_statistics": self.results["step_stats"],
            "failed_items": self.results["failed_items"],
            "processing_details": processing_results,
            "execution_time": datetime.now().isoformat()
        }
        
        summary_file = os.path.join(self.batch_dir, "batch_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*80}")
        print(f"📊 배치 처리 완료!")
        print(f"📁 결과 폴더: {self.batch_dir}")
        print(f"📈 성공률: {summary['execution_summary']['success_rate']}")
        print(f"✅ 성공: {self.results['success_count']}개")
        print(f"❌ 실패: {len(self.anime_list) - self.results['success_count']}개")
        print(f"💾 요약 파일: {summary_file}")
    
    def run_batch(self):
        """배치 처리 실행"""
        print(f"🚀 배치 처리 시작")
        start_time = datetime.now()
        
        # 환경 설정
        self.setup_batch_environment()
        
        # 애니메이션 목록 로드
        if not self.load_anime_list():
            return False
        
        # 각 애니메이션 처리
        processing_results = []
        
        for i, anime_title in enumerate(self.anime_list):
            result = self.process_single_anime(anime_title, i)
            processing_results.append(result)
            
            # 진행률 표시
            progress = ((i + 1) / len(self.anime_list)) * 100
            print(f"📊 진행률: {progress:.1f}% ({i+1}/{len(self.anime_list)})")
        
        # 요약 저장
        self.save_batch_summary(processing_results)
        
        end_time = datetime.now()
        duration = end_time - start_time
        print(f"⏱️ 총 소요시간: {duration}")
        
        return True

def main():
    parser = argparse.ArgumentParser(description='애니메이션 메타데이터 배치 처리')
    parser.add_argument('--csv', required=True, help='처리할 애니메이션 목록 CSV 파일')
    parser.add_argument('--description', default='', help='배치 처리 설명')
    parser.add_argument('--db-id', help='노션 데이터베이스 ID (기본값 사용하려면 생략)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv):
        print(f"❌ CSV 파일을 찾을 수 없습니다: {args.csv}")
        return 1
    
    processor = BatchProcessor(args.csv, args.description, args.db_id)
    
    try:
        success = processor.run_batch()
        return 0 if success else 1
    except KeyboardInterrupt:
        print(f"\n❌ 사용자에 의해 중단됨")
        return 1
    except Exception as e:
        print(f"❌ 배치 처리 실패: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
