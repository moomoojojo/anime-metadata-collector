#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
스크라이드 검색 결과 전체 확인
"""

import laftel

def test_scryed_full_search():
    """스크라이드 검색 결과 전체 확인"""
    
    search_term = "스크라이드"
    
    print(f"🔍 '{search_term}' 전체 검색 결과")
    print("="*80)
    
    try:
        # 라프텔 검색 수행
        search_results = laftel.sync.searchAnime(search_term)
        
        if not search_results:
            print("❌ 검색 결과가 없습니다.")
            return
        
        total_count = len(search_results)
        print(f"📊 총 검색 결과: {total_count}개")
        print()
        
        # 모든 결과 출력 (최대 20개)
        max_display = min(20, total_count)
        print(f"📋 상위 {max_display}개 결과:")
        print("-" * 80)
        
        for i, result in enumerate(search_results[:max_display]):
            try:
                print(f"#{i+1:2d}: {result.name}")
                print(f"      ID: {result.id}")
                print(f"      URL: {result.url}")
                print(f"      장르: {result.genres}")
                print(f"      성인물: {result.adultonly}")
                print(f"      이미지: {result.image}")
                print()
                
            except Exception as e:
                print(f"#{i+1:2d}: ❌ 결과 처리 실패: {e}")
                print()
        
        # 스크라이드 관련 제목 찾기
        print("🎯 스크라이드 관련 제목 분석:")
        print("-" * 40)
        
        scryed_related = []
        for i, result in enumerate(search_results[:max_display]):
            try:
                title = result.name
                if "스크라이드" in title:
                    scryed_related.append((i+1, title, result.id))
            except:
                pass
        
        if scryed_related:
            print(f"✅ 스크라이드 관련 제목 {len(scryed_related)}개 발견:")
            for rank, title, anime_id in scryed_related:
                print(f"   #{rank}: {title} (ID: {anime_id})")
        else:
            print("❌ 스크라이드 관련 제목 없음")
        
        print(f"\n📈 요약:")
        print(f"   총 결과: {total_count}개")
        print(f"   표시된 결과: {max_display}개")
        print(f"   스크라이드 관련: {len(scryed_related)}개")
        
    except Exception as e:
        print(f"❌ 검색 중 오류 발생: {e}")

if __name__ == "__main__":
    test_scryed_full_search()
