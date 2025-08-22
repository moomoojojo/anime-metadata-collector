#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
배치 처리 상태 확인 스크립트

사용법:
    python tools/check_status.py                    # 최신 배치 상태 확인
    python tools/check_status.py --batch-id BATCH_ID  # 특정 배치 상태 확인
    python tools/check_status.py --list             # 모든 배치 목록 보기
"""

import os
import json
import argparse
import glob
from datetime import datetime
from typing import Dict, Any, List

def find_latest_batch() -> str:
    """가장 최신 배치 ID 찾기"""
    production_dirs = glob.glob("productions/*/")
    if not production_dirs:
        return None
    
    # 가장 최신 폴더 반환
    latest_dir = max(production_dirs, key=os.path.getctime)
    return os.path.basename(latest_dir.rstrip('/'))

def load_batch_config(batch_id: str) -> Dict[str, Any]:
    """배치 설정 로드"""
    config_file = f"productions/{batch_id}/batch_config.json"
    if not os.path.exists(config_file):
        return {}
    
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_batch_summary(batch_id: str) -> Dict[str, Any]:
    """배치 요약 로드"""
    summary_file = f"productions/{batch_id}/batch_summary.json"
    if not os.path.exists(summary_file):
        return {}
    
    with open(summary_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_batch_files(batch_id: str) -> Dict[str, int]:
    """배치 폴더의 파일 수 확인"""
    batch_dir = f"productions/{batch_id}"
    
    return {
        "search_results": len(glob.glob(f"{batch_dir}/search_results/*.json")),
        "llm_results": len(glob.glob(f"{batch_dir}/llm_results/*.json")),
        "metadata_results": len(glob.glob(f"{batch_dir}/metadata_results/*.json")),
        "notion_results": len(glob.glob(f"{batch_dir}/notion_results/*.json"))
    }

def display_batch_status(batch_id: str, detailed: bool = True):
    """배치 상태 표시"""
    config = load_batch_config(batch_id)
    summary = load_batch_summary(batch_id)
    file_counts = check_batch_files(batch_id)
    
    print(f"\n{'='*80}")
    print(f"📊 배치 상태: {batch_id}")
    print(f"{'='*80}")
    
    if config:
        print(f"📅 실행 일시: {config.get('execution_date', 'Unknown')}")
        print(f"📝 설명: {config.get('description', 'No description')}")
        print(f"📋 소스 CSV: {config.get('source_csv', 'Unknown')}")
        print(f"🎯 총 항목 수: {config.get('total_items', 'Unknown')}")
        print(f"🗄️ 노션 DB: {config.get('notion_database_id', 'Default')}")
    
    if summary:
        exec_summary = summary.get('execution_summary', {})
        step_stats = summary.get('step_statistics', {})
        
        print(f"\n📈 실행 결과:")
        print(f"   ✅ 성공: {exec_summary.get('success_count', 0)}개")
        print(f"   ❌ 실패: {exec_summary.get('failed_count', 0)}개")
        print(f"   📊 성공률: {exec_summary.get('success_rate', '0%')}")
        
        print(f"\n🔄 단계별 통계:")
        print(f"   Step 1 (검색): {step_stats.get('step1_success', 0)}개 성공")
        print(f"   Step 2 (LLM): {step_stats.get('step2_success', 0)}개 성공")
        print(f"   Step 3 (메타데이터): {step_stats.get('step3_success', 0)}개 성공")
        print(f"   Step 4 (노션): {step_stats.get('step4_success', 0)}개 성공")
        
        failed_items = summary.get('failed_items', [])
        if failed_items and detailed:
            print(f"\n❌ 실패 항목들:")
            for item in failed_items:
                print(f"   - {item.get('title', 'Unknown')}: {item.get('reason', 'Unknown reason')}")
    
    print(f"\n📁 파일 수:")
    print(f"   🔍 검색 결과: {file_counts['search_results']}개")
    print(f"   🤖 LLM 결과: {file_counts['llm_results']}개")
    print(f"   📊 메타데이터: {file_counts['metadata_results']}개")
    print(f"   📝 노션 결과: {file_counts['notion_results']}개")
    
    batch_dir = f"productions/{batch_id}"
    print(f"\n📂 배치 폴더: {batch_dir}")

def list_all_batches():
    """모든 배치 목록 표시"""
    production_dirs = glob.glob("productions/*/")
    
    if not production_dirs:
        print("❌ 배치 처리 결과가 없습니다.")
        return
    
    print(f"\n📋 배치 처리 목록 ({len(production_dirs)}개)")
    print(f"{'='*80}")
    
    # 날짜순으로 정렬 (최신이 위에)
    sorted_dirs = sorted(production_dirs, key=os.path.getctime, reverse=True)
    
    for batch_dir in sorted_dirs:
        batch_id = os.path.basename(batch_dir.rstrip('/'))
        config = load_batch_config(batch_id)
        summary = load_batch_summary(batch_id)
        
        status = "🟢 완료" if summary else "🟡 진행중/미완료"
        success_count = summary.get('execution_summary', {}).get('success_count', 0) if summary else 0
        total_items = config.get('total_items', 0)
        
        print(f"{status} {batch_id}")
        print(f"   📅 {config.get('execution_date', 'Unknown')}")
        print(f"   📊 {success_count}/{total_items} 성공")
        print(f"   📝 {config.get('description', 'No description')}")
        print()

def main():
    parser = argparse.ArgumentParser(description='배치 처리 상태 확인')
    parser.add_argument('--batch-id', help='확인할 배치 ID')
    parser.add_argument('--list', action='store_true', help='모든 배치 목록 보기')
    parser.add_argument('--brief', action='store_true', help='간단한 정보만 표시')
    
    args = parser.parse_args()
    
    if args.list:
        list_all_batches()
        return
    
    if args.batch_id:
        batch_id = args.batch_id
    else:
        batch_id = find_latest_batch()
        if not batch_id:
            print("❌ 배치 처리 결과가 없습니다.")
            print("💡 먼저 batch_processor.py를 실행해보세요.")
            return
        print(f"📌 최신 배치 자동 선택: {batch_id}")
    
    batch_dir = f"productions/{batch_id}"
    if not os.path.exists(batch_dir):
        print(f"❌ 배치를 찾을 수 없습니다: {batch_id}")
        return
    
    display_batch_status(batch_id, detailed=not args.brief)

if __name__ == "__main__":
    main()
