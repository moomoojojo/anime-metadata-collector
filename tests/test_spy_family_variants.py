#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
스파이 패밀리 다양한 검색어 테스트
"""

from step1_search_candidates import collect_search_candidates

def test_spy_family_search():
    """스파이 패밀리 다양한 검색어로 테스트"""
    
    search_variants = [
        "스파이 패밀리",
        "SPY x FAMILY", 
        "SPY FAMILY",
        "spy family",
        "스파이패밀리"
    ]
    
    print("🧪 스파이 패밀리 검색어 변형 테스트")
    print("="*80)
    
    for i, search_term in enumerate(search_variants):
        print(f"\n🎯 테스트 #{i+1}: '{search_term}'")
        print("-" * 60)
        
        results = collect_search_candidates(search_term)
        
        if results.get("search_success"):
            candidates = results["candidate_titles"]
            total = results["total_results"]
            
            print(f"📊 총 {total}개 결과, 상위 {len(candidates)}개 후보:")
            
            # SPY x FAMILY 관련 제목 찾기
            spy_family_found = []
            for j, title in enumerate(candidates):
                if any(keyword in title.lower() for keyword in ["spy", "스파이"]):
                    if "패밀리" in title or "family" in title.lower():
                        spy_family_found.append((j+1, title))
                        print(f"   ✅ #{j+1}: {title}")
                    else:
                        print(f"   📺 #{j+1}: {title} (스파이 관련)")
                else:
                    print(f"   📺 #{j+1}: {title}")
            
            if spy_family_found:
                print(f"\n🎯 스파이 패밀리 관련 발견: {len(spy_family_found)}개")
                for rank, title in spy_family_found:
                    print(f"   - #{rank}: {title}")
            else:
                print("\n❌ 스파이 패밀리 관련 제목 없음")
                
        else:
            print("❌ 검색 실패")
        
        print()

if __name__ == "__main__":
    test_spy_family_search()
