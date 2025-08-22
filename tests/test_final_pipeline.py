#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최종 파이프라인 테스트: 전처리 + 자막판 우선
"""

import json
import os
from datetime import datetime
from step1_search_candidates import collect_search_candidates
from step2_llm_matching import perform_llm_matching
import config

def test_final_pipeline(user_input: str):
    """최종 파이프라인 테스트 (전처리 + 자막판 우선)"""
    
    print(f"\n🧪 최종 테스트: '{user_input}'")
    print("="*80)
    
    # 1단계: 라프텔 검색 (전처리 자동 적용)
    print(f"🔍 1단계: 라프텔 검색")
    search_results = collect_search_candidates(user_input)
    
    if not search_results.get("search_success", False):
        print("❌ 검색 실패")
        return {
            "user_input": user_input,
            "preprocessing_applied": search_results.get("preprocessing_applied", False),
            "search_success": False,
            "final_result": "검색 실패"
        }
    
    candidate_titles = search_results["candidate_titles"]
    preprocessing_applied = search_results.get("preprocessing_applied", False)
    
    print(f"📊 후보 수: {len(candidate_titles)}")
    
    # 자막/더빙 분석
    subtitle_count = sum(1 for title in candidate_titles if "(자막)" in title)
    dubbing_count = sum(1 for title in candidate_titles if "(더빙)" in title)
    
    print(f"📺 자막판: {subtitle_count}개, 더빙판: {dubbing_count}개")
    
    # 후보 미리보기 (상위 5개)
    print(f"\n🎯 상위 5개 후보:")
    for i, title in enumerate(candidate_titles[:5]):
        marker = ""
        if "(자막)" in title:
            marker = " 📺"
        elif "(더빙)" in title:
            marker = " 🎙️"
        print(f"   #{i+1}: {title}{marker}")
    if len(candidate_titles) > 5:
        print(f"   ... (총 {len(candidate_titles)}개)")
    
    # 2단계: LLM 매칭 (자막판 우선)
    print(f"\n🤖 2단계: OpenAI 매칭 (자막판 우선)")
    llm_results = perform_llm_matching(user_input, candidate_titles)
    
    # 결과 분석
    result_summary = {
        "user_input": user_input,
        "preprocessing_applied": preprocessing_applied,
        "search_success": True,
        "candidate_count": len(candidate_titles),
        "subtitle_count": subtitle_count,
        "dubbing_count": dubbing_count,
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
            
            # 자막판 우선 체크
            subtitle_preferred = "(자막)" in selected
            if subtitle_preferred:
                print(f"📺 ✅ 자막판 우선 선택 확인!")
            elif "(더빙)" in selected and subtitle_count > 0:
                print(f"🎙️ ⚠️  더빙판 선택 (자막판 {subtitle_count}개 있었음)")
            else:
                print(f"📹 일반판 선택 (자막/더빙 표시 없음)")
            
            result_summary.update({
                "final_result": "매칭 성공",
                "selected_title": selected,
                "confidence": confidence,
                "reason": reason,
                "subtitle_preferred": subtitle_preferred
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
    
    print("🚀 최종 파이프라인 테스트 시작")
    print("✨ 적용된 개선사항:")
    print("   - 검색어 전처리 (1기, 2기 등 제거)")
    print("   - 자막판 우선 선택")
    print("="*80)
    
    all_results = {}
    
    for user_input in test_cases:
        result = test_final_pipeline(user_input)
        all_results[user_input] = result
        print("\n" + "="*80)
    
    # 전체 결과 저장
    output_file = os.path.join(config.RESULTS_DIR, "final_pipeline_test.json")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"💾 최종 결과 저장: {output_file}")
    except Exception as e:
        print(f"❌ 저장 실패: {e}")
    
    # 최종 요약
    print(f"\n📊 최종 파이프라인 테스트 요약:")
    print("="*80)
    
    success_count = 0
    preprocessing_count = 0
    subtitle_preferred_count = 0
    
    for user_input, result in all_results.items():
        preprocessing = "✅" if result.get("preprocessing_applied", False) else "➖"
        final_result = result["final_result"]
        
        if result.get("preprocessing_applied", False):
            preprocessing_count += 1
        
        if final_result == "매칭 성공":
            success_count += 1
            status = f"✅ {final_result}"
            if "confidence" in result:
                status += f" ({result['confidence']}%)"
            
            # 자막판 우선 체크
            if result.get("subtitle_preferred", False):
                status += " 📺"
                subtitle_preferred_count += 1
            elif "(더빙)" in result.get("selected_title", ""):
                status += " 🎙️"
                
        elif final_result == "매칭 불가":
            status = f"⚠️ {final_result}"
        else:
            status = f"❌ {final_result}"
        
        print(f"{preprocessing} {user_input}")
        print(f"    → {status}")
        if "selected_title" in result:
            print(f"    → 선택: {result['selected_title']}")
        print()
    
    # 통계 요약
    total_cases = len(test_cases)
    print(f"📈 개선 효과 분석:")
    print(f"   ✅ 매칭 성공률: {success_count}/{total_cases} ({success_count/total_cases*100:.0f}%)")
    print(f"   🔧 전처리 적용: {preprocessing_count}/{total_cases} ({preprocessing_count/total_cases*100:.0f}%)")
    print(f"   📺 자막판 우선: {subtitle_preferred_count}/{success_count} (성공 케이스 중 {subtitle_preferred_count/max(success_count,1)*100:.0f}%)")
    
    print("\n✅ 최종 파이프라인 테스트 완료!")
    print("🎯 3단계 메타데이터 수집 준비 완료!")

if __name__ == "__main__":
    main()
