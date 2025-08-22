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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import step1_search_candidates
import step2_llm_matching
import step3_metadata_collection
import step4_notion_upload
import config

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
                result["final_status"] = "step2_failed"
                return result
            
            self.results["step_stats"]["step2_success"] += 1
            
            # Step 3: 메타데이터 수집
            print(f"\n📊 Step 3: 메타데이터 수집")
            
            # 임시로 결과 파일 경로 변경
            original_llm_file = config.LLM_CHOICE_FILE
            config.LLM_CHOICE_FILE = llm_file
            
            try:
                metadata_result = step3_metadata_collection.collect_metadata()
                
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
                
            finally:
                # 경로 복원
                config.LLM_CHOICE_FILE = original_llm_file
            
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
