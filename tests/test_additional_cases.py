#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
추가 테스트 케이스: 스파이 패밀리 1기, 스크라이드
"""

import json
import os
from datetime import datetime
from step1_search_candidates import collect_search_candidates
from step2_llm_matching import perform_llm_matching
import config

def test_case(user_input: str, case_name: str):
    """개별 테스트 케이스 실행"""
    print(f"\n🧪 {case_name} 테스트")
    print("="*80)
    print(f"📝 입력: {user_input}")
    
    # 1단계: 라프텔 검색
    print(f"\n🔍 1단계: 라프텔 검색")
    search_results = collect_search_candidates(user_input)
    
    if not search_results.get("search_success", False):
        print("❌ 검색 실패")
        return
    
    candidate_titles = search_results["candidate_titles"]
    print(f"📊 후보 수: {len(candidate_titles)}")
    
    # 후보 미리보기
    print(f"\n🎯 상위 5개 후보:")
    for i, title in enumerate(candidate_titles[:5]):
        print(f"   #{i+1}: {title}")
    if len(candidate_titles) > 5:
        print(f"   ... (총 {len(candidate_titles)}개)")
    
    # 2단계: LLM 매칭
    print(f"\n🤖 2단계: OpenAI 매칭")
    llm_results = perform_llm_matching(user_input, candidate_titles)
    
    # 결과 저장
    result_file = os.path.join(config.RESULTS_DIR, f"test_{case_name.lower().replace(' ', '_')}_result.json")
    combined_results = {
        "test_case": case_name,
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
    print(f"\n📊 {case_name} 결과 분석:")
    
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
            
            # 케이스별 정답 여부 판단
            is_correct = analyze_result(user_input, selected, case_name)
            if is_correct:
                print(f"\n🎉 정답! Assistant가 올바른 선택을 했습니다!")
            else:
                print(f"\n🤔 결과 검토 필요: 선택이 적절한지 확인이 필요합니다.")
                
        else:
            print(f"❌ 매칭 불가 판정")
            print(f"📝 이유: {reason}")
    else:
        print("❌ LLM 매칭 실패")
        if "error_message" in llm_results:
            print(f"오류: {llm_results['error_message']}")

def analyze_result(user_input: str, selected_title: str, case_name: str) -> bool:
    """케이스별 결과 분석"""
    
    if case_name == "스파이 패밀리 1기":
        # TV 시리즈를 선택했는지 확인 (극장판이 아닌)
        if "극장판" in selected_title or "코드" in selected_title:
            print("   ⚠️  극장판을 선택했습니다. TV 시리즈 1기가 더 적절할 수 있습니다.")
            return False
        elif "1기" in selected_title or ("스파이 패밀리" in selected_title and "2기" not in selected_title):
            return True
        else:
            return False
            
    elif case_name == "스크라이드":
        # 기본 제목이 포함되어 있고, 다른 작품이 아닌지 확인
        if "스크라이드" in selected_title:
            return True
        else:
            print("   ⚠️  다른 작품을 선택했거나 정확한 매칭을 찾지 못했습니다.")
            return False
    
    return True  # 기본값

def main():
    """메인 테스트 실행"""
    test_cases = [
        ("스파이 패밀리 1기", "스파이 패밀리 1기"),
        ("스크라이드", "스크라이드")
    ]
    
    print("🚀 추가 테스트 케이스 시작")
    print("="*80)
    
    for user_input, case_name in test_cases:
        test_case(user_input, case_name)
        print("\n" + "="*80)
    
    print("✅ 모든 추가 테스트 완료!")

if __name__ == "__main__":
    main()
