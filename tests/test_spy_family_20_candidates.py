#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
스파이 패밀리 1기 - 상위 20개 후보 테스트
"""

from step1_search_candidates import collect_search_candidates
from step2_llm_matching import perform_llm_matching

def test_spy_family_with_20_candidates():
    """스파이 패밀리 1기 - 상위 20개 후보로 재테스트"""
    
    user_input = "스파이 패밀리 1기"
    
    print("🧪 스파이 패밀리 1기 - 상위 20개 후보 테스트")
    print("="*80)
    print(f"📝 입력: {user_input}")
    print(f"🔧 수정: MAX_SEARCH_CANDIDATES = 20")
    
    # 1단계: 라프텔 검색 (20개 후보)
    search_results = collect_search_candidates(user_input)
    
    if not search_results.get("search_success"):
        print("❌ 검색 실패")
        return
    
    candidate_titles = search_results["candidate_titles"]
    print(f"\n📊 수집된 후보 수: {len(candidate_titles)}")
    
    # 자막/더빙 분석
    subtitle_titles = [title for title in candidate_titles if "(자막)" in title]
    dubbing_titles = [title for title in candidate_titles if "(더빙)" in title]
    
    print(f"📺 자막판: {len(subtitle_titles)}개")
    print(f"🎙️ 더빙판: {len(dubbing_titles)}개")
    
    # SPY×FAMILY part 1 찾기
    spy_family_part1_candidates = []
    for i, title in enumerate(candidate_titles):
        if "SPY×FAMILY part 1" in title or "SPY FAMILY part 1" in title:
            spy_family_part1_candidates.append((i+1, title))
    
    print(f"\n🎯 SPY×FAMILY part 1 관련 후보:")
    if spy_family_part1_candidates:
        for rank, title in spy_family_part1_candidates:
            marker = "📺" if "(자막)" in title else "🎙️" if "(더빙)" in title else "📹"
            print(f"   #{rank}: {title} {marker}")
        
        # 자막판 SPY×FAMILY part 1 체크
        subtitle_part1 = [title for rank, title in spy_family_part1_candidates if "(자막)" in title]
        if subtitle_part1:
            print(f"\n✅ 자막판 SPY×FAMILY part 1 발견!")
            for title in subtitle_part1:
                print(f"   🎯 {title}")
        else:
            print(f"\n⚠️ 자막판 SPY×FAMILY part 1 없음 (더빙판만 있음)")
    else:
        print("   ❌ SPY×FAMILY part 1 관련 후보 없음")
    
    # 2단계: LLM 매칭
    print(f"\n🤖 2단계: OpenAI 매칭 (자막판 우선)")
    llm_results = perform_llm_matching(user_input, candidate_titles)
    
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
            
            # 자막판 여부 체크
            if "(자막)" in selected:
                print(f"\n📺 ✅ 자막판 선택 성공!")
            elif "(더빙)" in selected:
                print(f"\n🎙️ 더빙판 선택 (자막판 없었음)")
            else:
                print(f"\n📹 일반판 선택")
                
        else:
            reason = llm_results.get("reason")
            print(f"❌ 매칭 불가: {reason}")
    else:
        print("❌ LLM 매칭 실패")
    
    print(f"\n📊 결론:")
    print(f"   후보 확장 효과: 10개 → 20개")
    if spy_family_part1_candidates:
        print(f"   SPY×FAMILY part 1 발견: ✅")
        if subtitle_part1:
            print(f"   자막판 발견: ✅")
        else:
            print(f"   자막판 발견: ❌ (더빙판만)")
    else:
        print(f"   SPY×FAMILY part 1 발견: ❌")

if __name__ == "__main__":
    test_spy_family_with_20_candidates()
