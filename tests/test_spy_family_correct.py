#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
스파이 패밀리 올바른 검색어로 LLM 매칭 테스트
"""

import json
import os
from step1_search_candidates import collect_search_candidates  
from step2_llm_matching import perform_llm_matching
import config

def test_spy_family_correct():
    """스파이 패밀리 올바른 검색으로 LLM 테스트"""
    
    # 원래 사용자 의도
    original_input = "스파이 패밀리 1기"
    
    # 올바른 검색어 (SPY×FAMILY part 1이 나오는 검색어)
    search_term = "스파이 패밀리"
    
    print("🧪 스파이 패밀리 1기 - 올바른 검색어 테스트")
    print("="*80)
    print(f"📝 사용자 의도: {original_input}")
    print(f"🔍 실제 검색어: {search_term}")
    
    # 1단계: 올바른 검색어로 검색
    print(f"\n🔍 1단계: 라프텔 검색")
    search_results = collect_search_candidates(search_term)
    
    if not search_results.get("search_success"):
        print("❌ 검색 실패")
        return
    
    candidate_titles = search_results["candidate_titles"]
    print(f"📊 후보 수: {len(candidate_titles)}")
    
    # SPY×FAMILY part 1 확인
    part1_found = False
    for i, title in enumerate(candidate_titles):
        if "SPY×FAMILY part 1" in title:
            print(f"✅ SPY×FAMILY part 1 발견: #{i+1} {title}")
            part1_found = True
    
    if not part1_found:
        print("❌ SPY×FAMILY part 1이 후보에 없음")
        return
    
    # 2단계: LLM 매칭 (원래 사용자 의도로)
    print(f"\n🤖 2단계: OpenAI 매칭")
    print(f"   입력: {original_input} (사용자 원래 의도)")
    print(f"   후보: 실제 검색 결과")
    
    llm_results = perform_llm_matching(original_input, candidate_titles)
    
    # 결과 저장
    result_file = os.path.join(config.RESULTS_DIR, "spy_family_correct_test.json")
    combined_results = {
        "original_input": original_input,
        "search_term": search_term,
        "search_results": search_results,
        "llm_results": llm_results
    }
    
    try:
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(combined_results, f, ensure_ascii=False, indent=2)
        print(f"💾 결과 저장: {result_file}")
    except Exception as e:
        print(f"❌ 저장 실패: {e}")
    
    # 결과 분석
    print(f"\n📊 스파이 패밀리 1기 재테스트 결과:")
    
    if llm_results.get("matching_success"):
        selected = llm_results.get("selected_title")
        confidence = llm_results.get("confidence")
        reason = llm_results.get("reason")
        match_status = llm_results.get("match_status")
        
        if match_status == "match_found":
            print(f"✅ 매칭 성공!")
            print(f"🎯 선택: {selected}")
            print(f"🔍 신뢰도: {confidence}%")
            print(f"📝 이유: {reason}")
            
            # 정답 확인
            if "SPY×FAMILY part 1" in selected:
                print(f"\n🎉 정답! Assistant가 올바른 1기를 선택했습니다!")
                print(f"💡 결론: 검색어 개선으로 문제 해결!")
            else:
                print(f"\n🤔 다른 선택: {selected}")
                
        else:
            print(f"❌ 매칭 불가 판정")
            print(f"📝 이유: {reason}")
    else:
        print("❌ LLM 매칭 실패")

if __name__ == "__main__":
    test_spy_family_correct()
