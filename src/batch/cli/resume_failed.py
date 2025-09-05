#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실패한 항목 재처리 스크립트

사용법:
    python tools/resume_failed.py                    # 최신 배치의 실패 항목 재처리
    python tools/resume_failed.py --batch-id BATCH_ID  # 특정 배치의 실패 항목 재처리
    python tools/resume_failed.py --dry-run          # 실제 실행 없이 실패 항목만 확인
"""

import os
import sys
import json
import argparse
import glob
from datetime import datetime
from typing import List, Dict, Any

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.anime_metadata import step1_search_candidates
from src.anime_metadata import step2_llm_matching
from src.anime_metadata import step3_metadata_collection
from src.anime_metadata import step4_notion_upload
from src.anime_metadata import config

def find_latest_batch() -> str:
    """가장 최신 배치 ID 찾기"""
    production_dirs = glob.glob("productions/*/")
    if not production_dirs:
        return None
    
    latest_dir = max(production_dirs, key=os.path.getctime)
    return os.path.basename(latest_dir.rstrip('/'))

def load_batch_summary(batch_id: str) -> Dict[str, Any]:
    """배치 요약 로드"""
    summary_file = f"productions/{batch_id}/batch_summary.json"
    if not os.path.exists(summary_file):
        return {}
    
    with open(summary_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_failed_items(batch_id: str) -> List[Dict[str, Any]]:
    """실패한 항목들 찾기"""
    summary = load_batch_summary(batch_id)
    if not summary:
        print(f"❌ 배치 요약을 찾을 수 없습니다: {batch_id}")
        return []
    
    processing_details = summary.get('processing_details', [])
    failed_items = []
    
    for detail in processing_details:
        if detail.get('final_status') != 'success':
            failed_items.append(detail)
    
    return failed_items

def analyze_failure_reason(item: Dict[str, Any]) -> str:
    """실패 원인 분석"""
    final_status = item.get('final_status', 'unknown')
    
    if final_status == 'step1_failed':
        return "검색 결과 없음"
    elif final_status == 'step2_failed':
        return "LLM 매칭 실패"
    elif final_status == 'step3_failed':
        return "메타데이터 수집 실패"
    elif final_status == 'step4_failed':
        return "노션 업로드 실패"
    elif final_status == 'error':
        return f"시스템 오류: {item.get('error', 'Unknown')}"
    else:
        return "알 수 없는 오류"

def get_resume_step(item: Dict[str, Any]) -> int:
    """어느 단계부터 재시작할지 결정"""
    final_status = item.get('final_status', 'unknown')
    
    if final_status == 'step1_failed':
        return 1
    elif final_status == 'step2_failed':
        return 2
    elif final_status == 'step3_failed':
        return 3
    elif final_status == 'step4_failed':
        return 4
    else:
        return 1  # 기본적으로 처음부터

def resume_single_item(batch_id: str, item: Dict[str, Any], dry_run: bool = False) -> bool:
    """단일 항목 재처리"""
    anime_title = item.get('anime_title', '')
    index = item.get('index', 0)
    resume_step = get_resume_step(item)
    
    print(f"\n🔄 재처리 중: {anime_title}")
    print(f"   📍 Step {resume_step}부터 시작")
    
    if dry_run:
        print(f"   🧪 [DRY RUN] 실제 실행하지 않음")
        return True
    
    batch_dir = f"productions/{batch_id}"
    
    try:
        # 결과 저장 경로들
        search_dir = os.path.join(batch_dir, "search_results")
        llm_dir = os.path.join(batch_dir, "llm_results")
        metadata_dir = os.path.join(batch_dir, "metadata_results")
        notion_dir = os.path.join(batch_dir, "notion_results")
        
        search_result = None
        llm_result = None
        metadata_result = None
        
        # Step 1부터 시작하는 경우
        if resume_step <= 1:
            print(f"   🔍 Step 1: 검색 후보 수집")
            search_result = step1_search_candidates.collect_search_candidates(anime_title)
            
            search_file = os.path.join(search_dir, f"search_{index:02d}_{anime_title.replace('/', '_')}.json")
            with open(search_file, 'w', encoding='utf-8') as f:
                json.dump(search_result, f, ensure_ascii=False, indent=2)
            
            if not search_result.get("search_success"):
                print(f"   ❌ Step 1 재실패")
                return False
        
        # Step 2부터 시작하는 경우 (기존 검색 결과 로드)
        if resume_step <= 2:
            if not search_result:
                search_file = os.path.join(search_dir, f"search_{index:02d}_{anime_title.replace('/', '_')}.json")
                if os.path.exists(search_file):
                    with open(search_file, 'r', encoding='utf-8') as f:
                        search_result = json.load(f)
                else:
                    print(f"   ❌ 기존 검색 결과를 찾을 수 없음")
                    return False
            
            print(f"   🤖 Step 2: LLM 매칭")
            llm_result = step2_llm_matching.perform_llm_matching(
                anime_title, 
                search_result["candidate_titles"]
            )
            
            llm_file = os.path.join(llm_dir, f"llm_{index:02d}_{anime_title.replace('/', '_')}.json")
            with open(llm_file, 'w', encoding='utf-8') as f:
                json.dump(llm_result, f, ensure_ascii=False, indent=2)
            
            if not llm_result.get("matching_success") or llm_result.get("match_status") != "match_found":
                print(f"   ❌ Step 2 재실패")
                return False
        
        # Step 3부터 시작하는 경우 (기존 LLM 결과 로드)
        if resume_step <= 3:
            if not llm_result:
                llm_file = os.path.join(llm_dir, f"llm_{index:02d}_{anime_title.replace('/', '_')}.json")
                if os.path.exists(llm_file):
                    with open(llm_file, 'r', encoding='utf-8') as f:
                        llm_result = json.load(f)
                else:
                    print(f"   ❌ 기존 LLM 결과를 찾을 수 없음")
                    return False
            
            print(f"   📊 Step 3: 메타데이터 수집")
            
            # 임시로 결과 파일 경로 변경
            original_llm_file = config.LLM_CHOICE_FILE
            llm_file = os.path.join(llm_dir, f"llm_{index:02d}_{anime_title.replace('/', '_')}.json")
            config.LLM_CHOICE_FILE = llm_file
            
            try:
                metadata_result = step3_metadata_collection.collect_metadata()
                
                metadata_file = os.path.join(metadata_dir, f"metadata_{index:02d}_{anime_title.replace('/', '_')}.json")
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata_result, f, ensure_ascii=False, indent=2)
                
                if not metadata_result.get("metadata_success"):
                    print(f"   ❌ Step 3 재실패")
                    return False
                    
            finally:
                config.LLM_CHOICE_FILE = original_llm_file
        
        # Step 4 (노션 업로드)
        if resume_step <= 4:
            if not metadata_result:
                metadata_file = os.path.join(metadata_dir, f"metadata_{index:02d}_{anime_title.replace('/', '_')}.json")
                if os.path.exists(metadata_file):
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata_result = json.load(f)
                else:
                    print(f"   ❌ 기존 메타데이터를 찾을 수 없음")
                    return False
            
            print(f"   📝 Step 4: 노션 업로드")
            
            notion_result = step4_notion_upload.upload_to_notion(
                metadata_result["metadata"], 
                anime_title
            )
            
            notion_file = os.path.join(notion_dir, f"notion_{index:02d}_{anime_title.replace('/', '_')}.json")
            notion_result["upload_timestamp"] = datetime.now().isoformat()
            notion_result["user_input"] = anime_title
            
            with open(notion_file, 'w', encoding='utf-8') as f:
                json.dump(notion_result, f, ensure_ascii=False, indent=2)
            
            if not notion_result.get("upload_success"):
                print(f"   ❌ Step 4 재실패")
                return False
        
        print(f"   ✅ 재처리 성공!")
        return True
        
    except Exception as e:
        print(f"   ❌ 재처리 중 오류: {e}")
        return False

def update_batch_summary(batch_id: str):
    """배치 요약 업데이트 (재처리 후)"""
    # TODO: 재처리 후 요약 파일 업데이트 로직
    # 현재는 수동으로 check_status.py를 다시 실행해야 함
    print(f"💡 재처리 완료 후 상태 확인: python tools/check_status.py --batch-id {batch_id}")

def main():
    parser = argparse.ArgumentParser(description='실패한 항목 재처리')
    parser.add_argument('--batch-id', help='재처리할 배치 ID')
    parser.add_argument('--dry-run', action='store_true', help='실제 실행 없이 확인만')
    parser.add_argument('--item', help='특정 항목만 재처리 (애니메이션 제목)')
    
    args = parser.parse_args()
    
    # 배치 ID 결정
    if args.batch_id:
        batch_id = args.batch_id
    else:
        batch_id = find_latest_batch()
        if not batch_id:
            print("❌ 배치 처리 결과가 없습니다.")
            return
        print(f"📌 최신 배치 자동 선택: {batch_id}")
    
    # 배치 폴더 확인
    batch_dir = f"productions/{batch_id}"
    if not os.path.exists(batch_dir):
        print(f"❌ 배치를 찾을 수 없습니다: {batch_id}")
        return
    
    # 실패 항목 찾기
    failed_items = find_failed_items(batch_id)
    
    if not failed_items:
        print(f"✅ 재처리할 실패 항목이 없습니다.")
        return
    
    print(f"\n📊 실패 항목 분석:")
    print(f"   총 실패: {len(failed_items)}개")
    
    # 특정 항목 재처리
    if args.item:
        target_item = None
        for item in failed_items:
            if args.item in item.get('anime_title', ''):
                target_item = item
                break
        
        if not target_item:
            print(f"❌ 해당 항목을 찾을 수 없습니다: {args.item}")
            return
        
        failed_items = [target_item]
    
    # 실패 항목 목록 표시
    for i, item in enumerate(failed_items, 1):
        anime_title = item.get('anime_title', 'Unknown')
        reason = analyze_failure_reason(item)
        resume_step = get_resume_step(item)
        
        print(f"   {i}. {anime_title}")
        print(f"      원인: {reason}")
        print(f"      재시작: Step {resume_step}")
    
    if args.dry_run:
        print(f"\n🧪 [DRY RUN] 실제 재처리는 수행하지 않습니다.")
        return
    
    # 사용자 확인
    response = input(f"\n❓ {len(failed_items)}개 항목을 재처리하시겠습니까? (y/N): ")
    if response.lower() != 'y':
        print("❌ 재처리가 취소되었습니다.")
        return
    
    # 재처리 실행
    print(f"\n🔄 재처리 시작...")
    success_count = 0
    
    for item in failed_items:
        if resume_single_item(batch_id, item):
            success_count += 1
    
    print(f"\n📊 재처리 완료:")
    print(f"   ✅ 성공: {success_count}/{len(failed_items)}")
    print(f"   ❌ 재실패: {len(failed_items) - success_count}")
    
    if success_count > 0:
        update_batch_summary(batch_id)

if __name__ == "__main__":
    main()
