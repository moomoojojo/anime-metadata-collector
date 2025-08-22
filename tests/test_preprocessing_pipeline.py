#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
검색어 전처리 파이프라인 테스트
"""

import json
import os
import re
from datetime import datetime
from step1_search_candidates import collect_search_candidates
from step2_llm_matching import perform_llm_matching
import config

def optimize_search_term(user_input: str) -> str:
    """라프텔 검색 최적화를 위한 검색어 전처리"""
    
    # 시즌 정보 패턴들
    season_patterns = [
        r'\s*1기\s*$',          # "스파이 패밀리 1기" → "스파이 패밀리"
        r'\s*2기\s*$',          # "무직전생 2기" → "무직전생"  
        r'\s*3기\s*$',          # "애니 3기" → "애니"
        r'\s*4기\s*$',          # "애니 4기" → "애니"
        r'\s*시즌\s*\d+\s*$',   # "애니 시즌 2" → "애니"
        r'\s*Season\s*\d+\s*$', # "애니 Season 2" → "애니"
    ]
    
    original_input = user_input
    optimized_input = user_input
    
    # 패턴 매칭해서 시즌 정보 제거
    for pattern in season_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            optimized_input = re.sub(pattern, '', user_input, flags=re.IGNORECASE).strip()
            break
    
    return optimized_input

def test_preprocessing_pipeline(user_input: str):
    """검색어 전처리 파이프라인 전체 테스트"""
    
    print(f"\n🧪 테스트 케이스: '{user_input}'")
    print("="*80)
    
    # 1단계: 검색어 전처리
    search_term = optimize_search_term(user_input)
    
    if search_term != user_input:
        print(f"🔧 전처리 적용됨:")
        print(f"   원본: {user_input}")
        print(f"   검색어: {search_term}")
    else:
        print(f"🔧 전처리 없음 (원본 그대로)")
        print(f"   검색어: {search_term}")
    
    # 2단계: 라프텔 검색
    print(f"\n🔍 1단계: 라프텔 검색")
    search_results = collect_search_candidates(search_term)
    
    if not search_results.get("search_success", False):
        print("❌ 검색 실패")
        return {
            "user_input": user_input,
            "search_term": search_term,
            "preprocessing_applied": search_term != user_input,
            "search_success": False,
            "final_result": "검색 실패"
        }
    
    candidate_titles = search_results["candidate_titles"]
    print(f"📊 후보 수: {len(candidate_titles)}")
    
    # 후보 미리보기 (상위 5개)
    print(f"\n🎯 상위 5개 후보:")
    for i, title in enumerate(candidate_titles[:5]):
        print(f"   #{i+1}: {title}")
    if len(candidate_titles) > 5:
        print(f"   ... (총 {len(candidate_titles)}개)")
    
    # 3단계: LLM 매칭 (원본 사용자 입력으로)
    print(f"\n🤖 2단계: OpenAI 매칭")
    print(f"   매칭 기준: {user_input} (원본 의도)")
    
    llm_results = perform_llm_matching(user_input, candidate_titles)
    
    # 결과 분석
    result_summary = {
        "user_input": user_input,
        "search_term": search_term,
        "preprocessing_applied": search_term != user_input,
        "search_success": True,
        "candidate_count": len(candidate_titles),
        "llm_success": llm_results.get("matching_success", False)
    }
    
    if llm_results.get("matching_success"):
        match_status = llm_results.get("match_status")
        if match_status == "match_found":
            selected = llm_results.get("selected_title")
            confidence = llm_results.get("confidence")
            reason = llm_results.get("reason")
            
            print(f"✅ 매칭 성공!")
            print(f"🎯 선택: {selected}")
            print(f"🔍 신뢰도: {confidence}%")
            print(f"📝 이유: {reason}")
            
            result_summary.update({
                "final_result": "매칭 성공",
                "selected_title": selected,
                "confidence": confidence,
                "reason": reason
            })
            
        else:
            reason = llm_results.get("reason")
            print(f"❌ 매칭 불가")
            print(f"📝 이유: {reason}")
            
            result_summary.update({
                "final_result": "매칭 불가",
                "reason": reason
            })
    else:
        print("❌ LLM 매칭 실패")
        result_summary["final_result"] = "LLM 실패"
    
    return result_summary

def main():
    """메인 테스트 함수"""
    
    test_cases = [
        "Re: 제로부터 시작하는 이세계 생활 3기",
        "스파이 패밀리 1기", 
        "무직전생 1기",
        "스크라이드"
    ]
    
    print("🚀 검색어 전처리 파이프라인 테스트 시작")
    print("="*80)
    print("📋 테스트 케이스:")
    for i, case in enumerate(test_cases):
        print(f"   {i+1}. {case}")
    
    all_results = {}
    
    for user_input in test_cases:
        result = test_preprocessing_pipeline(user_input)
        all_results[user_input] = result
        print("\n" + "="*80)
    
    # 전체 결과 저장
    output_file = os.path.join(config.RESULTS_DIR, "preprocessing_pipeline_test.json")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"💾 전체 결과 저장: {output_file}")
    except Exception as e:
        print(f"❌ 저장 실패: {e}")
    
    # 최종 요약
    print(f"\n📊 전처리 파이프라인 테스트 요약:")
    print("="*80)
    
    for user_input, result in all_results.items():
        preprocessing = "✅" if result["preprocessing_applied"] else "➖"
        final_result = result["final_result"]
        
        if final_result == "매칭 성공":
            status = f"✅ {final_result}"
            if "confidence" in result:
                status += f" ({result['confidence']}%)"
        elif final_result == "매칭 불가":
            status = f"⚠️ {final_result}"
        else:
            status = f"❌ {final_result}"
        
        print(f"{preprocessing} {user_input}")
        print(f"    → {status}")
        if "selected_title" in result:
            print(f"    → 선택: {result['selected_title']}")
        print()
    
    print("✅ 전처리 파이프라인 테스트 완료!")

if __name__ == "__main__":
    main()
