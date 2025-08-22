#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1단계 → 2단계 → 3단계 전체 파이프라인 테스트
"""

import json
import os
from step1_search_candidates import collect_search_candidates
from step2_llm_matching import perform_llm_matching
from step3_metadata_collection import collect_metadata, find_anime_id_by_title, fetch_detailed_metadata
import config

def test_full_pipeline(user_input: str):
    """1→2→3단계 전체 파이프라인 테스트"""
    
    print(f"\n🚀 전체 파이프라인 테스트: '{user_input}'")
    print("="*80)
    
    # 1단계: 라프텔 검색
    print(f"🔍 1단계: 라프텔 검색")
    search_results = collect_search_candidates(user_input)
    
    if not search_results.get("search_success", False):
        return {
            "user_input": user_input,
            "step1_success": False,
            "final_result": "1단계 검색 실패"
        }
    
    candidate_titles = search_results["candidate_titles"]
    print(f"✅ 1단계 성공: {len(candidate_titles)}개 후보")
    
    # 2단계: LLM 매칭
    print(f"\n🤖 2단계: LLM 매칭")
    llm_results = perform_llm_matching(user_input, candidate_titles)
    
    if not llm_results.get("matching_success", False):
        return {
            "user_input": user_input,
            "step1_success": True,
            "step2_success": False,
            "candidate_count": len(candidate_titles),
            "final_result": "2단계 매칭 실패"
        }
    
    match_status = llm_results.get("match_status")
    if match_status != "match_found":
        return {
            "user_input": user_input,
            "step1_success": True,
            "step2_success": True,
            "step2_result": "매칭 불가",
            "step2_reason": llm_results.get("reason", ""),
            "candidate_count": len(candidate_titles),
            "final_result": "2단계 매칭 불가"
        }
    
    selected_title = llm_results["selected_title"]
    confidence = llm_results.get("confidence", 0)
    print(f"✅ 2단계 성공: {selected_title} ({confidence}%)")
    
    # 3단계: 메타데이터 수집
    print(f"\n📊 3단계: 메타데이터 수집")
    
    # 애니메이션 ID 찾기
    anime_id = find_anime_id_by_title(selected_title, user_input)
    if not anime_id:
        return {
            "user_input": user_input,
            "step1_success": True,
            "step2_success": True,
            "step2_result": "매칭 성공",
            "selected_title": selected_title,
            "confidence": confidence,
            "step3_success": False,
            "step3_error": "애니메이션 ID 없음",
            "candidate_count": len(candidate_titles),
            "final_result": "3단계 ID 검색 실패"
        }
    
    print(f"✅ 애니메이션 ID 발견: {anime_id}")
    
    # 메타데이터 수집
    metadata = fetch_detailed_metadata(anime_id)
    if not metadata:
        return {
            "user_input": user_input,
            "step1_success": True,
            "step2_success": True,
            "step2_result": "매칭 성공",
            "selected_title": selected_title,
            "confidence": confidence,
            "anime_id": anime_id,
            "step3_success": False,
            "step3_error": "메타데이터 수집 실패",
            "candidate_count": len(candidate_titles),
            "final_result": "3단계 메타데이터 실패"
        }
    
    print(f"✅ 3단계 성공: 메타데이터 수집 완료")
    
    return {
        "user_input": user_input,
        "step1_success": True,
        "step2_success": True,
        "step3_success": True,
        "step2_result": "매칭 성공",
        "selected_title": selected_title,
        "confidence": confidence,
        "anime_id": anime_id,
        "metadata": metadata,
        "candidate_count": len(candidate_titles),
        "final_result": "전체 파이프라인 성공"
    }

def main():
    """메인 테스트 함수"""
    
    test_cases = [
        "Re: 제로부터 시작하는 이세계 생활 3기",
        "스파이 패밀리 1기", 
        "무직전생 1기",
        "스크라이드"
    ]
    
    print("🚀 1→2→3단계 전체 파이프라인 테스트")
    print("="*80)
    
    all_results = {}
    
    for user_input in test_cases:
        result = test_full_pipeline(user_input)
        all_results[user_input] = result
        print("\n" + "="*80)
    
    # 결과 저장
    output_file = os.path.join(config.RESULTS_DIR, "full_pipeline_1_to_3_test.json")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"💾 전체 결과 저장: {output_file}")
    except Exception as e:
        print(f"❌ 저장 실패: {e}")
    
    # 최종 요약
    print(f"\n📊 전체 파이프라인 테스트 요약:")
    print("="*80)
    
    success_count = 0
    step3_success_count = 0
    
    for user_input, result in all_results.items():
        final_result = result["final_result"]
        
        if "성공" in final_result:
            success_count += 1
            if result.get("step3_success", False):
                step3_success_count += 1
            status_icon = "✅"
        elif "불가" in final_result:
            status_icon = "⚠️"
        else:
            status_icon = "❌"
        
        print(f"{status_icon} {user_input}")
        print(f"    → {final_result}")
        
        if result.get("step3_success"):
            metadata = result["metadata"]
            print(f"    → 제목: {metadata['name']}")
            print(f"    → 방영분기: {metadata['air_year_quarter']}")
            print(f"    → 평점: {metadata['avg_rating']}")
            print(f"    → 총 화수: {metadata['total_episodes']}화")
        elif result.get("step2_success") and result.get("step2_result") == "매칭 성공":
            print(f"    → 선택: {result['selected_title']}")
        
        print()
    
    total_cases = len(test_cases)
    print(f"📈 파이프라인 성능:")
    print(f"   ✅ 전체 성공률: {success_count}/{total_cases} ({success_count/total_cases*100:.0f}%)")
    print(f"   📊 3단계 성공률: {step3_success_count}/{total_cases} ({step3_success_count/total_cases*100:.0f}%)")
    
    if step3_success_count > 0:
        print(f"\n🎯 4단계 노션 업로드 준비 완료!")
        print(f"   성공한 {step3_success_count}개 케이스로 노션 페이지 생성 가능")
    
    print("\n✅ 전체 파이프라인 테스트 완료!")

if __name__ == "__main__":
    main()
