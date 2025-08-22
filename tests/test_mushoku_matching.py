#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
무직전생 1기 케이스 테스트용 스크립트
"""

import json
import os
from datetime import datetime
from step2_llm_matching import perform_llm_matching, save_llm_results
import config

def test_mushoku_case():
    """무직전생 1기 케이스 테스트"""
    
    # 무직전생 검색 결과 (1단계에서 확인된 실제 데이터)
    user_input = "무직전생 ~이세계에 갔으면 최선을 다한다~ 1기"
    candidate_titles = [
        "무직전생 II ~이세계에 갔으면 최선을 다한다~ part 2",  # 2기
        "무직전생  ~이세계에 갔으면 최선을 다한다~ Part 1",      # 1기 ✅
        "무직전생 II ~이세계에 갔으면 최선을 다한다~ part 1",   # 2기
        "무직전생 ~이세계에 갔으면 최선을 다한다~  Part 2",      # 1기 part 2
        "(더빙) 이누야샤 1기",
        "치하야후루 1기",
        "(더빙) 마도조사 1기",
        "(더빙) 원피스 1기",
        "프리파라 1기",
        "(자막) 이누야샤 1기"
    ]
    
    print("🧪 무직전생 1기 매칭 테스트")
    print("="*80)
    print(f"📝 입력: {user_input}")
    print(f"📊 후보 수: {len(candidate_titles)}")
    print("\n🎯 핵심 후보들:")
    print("   #1: 무직전생 II part 2 (2기)")
    print("   #2: 무직전생 Part 1 ✅ (정답 - 1기)")
    print("   #3: 무직전생 II part 1 (2기)")
    print("\n🤖 Assistant가 2번을 올바르게 선택할 수 있을까요?")
    print("="*80)
    
    # LLM 매칭 수행
    llm_results = perform_llm_matching(user_input, candidate_titles)
    
    # 결과 저장
    mushoku_result_file = os.path.join(config.RESULTS_DIR, "mushoku_test_result.json")
    try:
        with open(mushoku_result_file, 'w', encoding='utf-8') as f:
            json.dump(llm_results, f, ensure_ascii=False, indent=2)
        print(f"💾 무직전생 테스트 결과 저장: {mushoku_result_file}")
    except Exception as e:
        print(f"❌ 저장 실패: {e}")
    
    # 결과 분석
    print("\n" + "="*80)
    print("📊 무직전생 테스트 결과 분석:")
    
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
            if "Part 1" in selected and "II" not in selected:
                print("\n🎉 정답! Assistant가 올바른 1기를 선택했습니다!")
            else:
                print(f"\n❌ 오답! 1기가 아닌 다른 작품을 선택했습니다.")
                print("   올바른 선택: '무직전생 ~이세계에 갔으면 최선을 다한다~ Part 1'")
        else:
            print(f"❌ 매칭 불가 판정")
            print(f"📝 이유: {reason}")
    else:
        print("❌ LLM 매칭 실패")
        if "error_message" in llm_results:
            print(f"오류: {llm_results['error_message']}")

if __name__ == "__main__":
    test_mushoku_case()
