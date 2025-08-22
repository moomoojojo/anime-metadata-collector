#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
스파이 패밀리 검색어 비교 분석
"""

import json
import laftel
from datetime import datetime

def detailed_search_analysis(search_term: str, max_results: int = 20):
    """라프텔 검색 상세 분석"""
    
    print(f"\n🔍 검색어: '{search_term}'")
    print("="*80)
    
    try:
        # 라프텔 검색 수행
        search_results = laftel.sync.searchAnime(search_term)
        
        if not search_results:
            print("❌ 검색 결과가 없습니다.")
            return {
                "search_term": search_term,
                "total_results": 0,
                "results": [],
                "search_success": False
            }
        
        total_count = len(search_results)
        print(f"📊 총 검색 결과: {total_count}개")
        
        # 상위 N개 또는 전체 결과 수집
        results_to_show = min(max_results, total_count)
        print(f"📋 표시할 결과: {results_to_show}개")
        
        detailed_results = []
        
        for i, result in enumerate(search_results[:results_to_show]):
            try:
                result_info = {
                    "rank": i + 1,
                    "name": result.name,
                    "id": result.id,
                    "url": result.url,
                    "image": result.image,
                    "genres": result.genres,
                    "adult_only": result.adultonly
                }
                detailed_results.append(result_info)
                
                print(f"#{i+1:2d}: {result.name}")
                print(f"      ID: {result.id}")
                print(f"      URL: {result.url}")
                print(f"      장르: {result.genres}")
                print(f"      성인물: {result.adultonly}")
                print()
                
            except Exception as e:
                print(f"❌ 결과 #{i+1} 처리 실패: {e}")
                detailed_results.append({
                    "rank": i + 1,
                    "error": str(e)
                })
        
        return {
            "search_term": search_term,
            "search_timestamp": datetime.now().isoformat(),
            "total_results": total_count,
            "displayed_results": results_to_show,
            "results": detailed_results,
            "search_success": True
        }
        
    except Exception as e:
        print(f"❌ 검색 중 오류 발생: {e}")
        return {
            "search_term": search_term,
            "total_results": 0,
            "results": [],
            "search_success": False,
            "error": str(e)
        }

def compare_spy_family_searches():
    """스파이 패밀리 검색어 비교"""
    
    search_terms = [
        "스파이 패밀리",
        "스파이 패밀리 1기"
    ]
    
    print("🚀 스파이 패밀리 검색어 비교 분석 시작")
    print("="*80)
    
    all_results = {}
    
    for search_term in search_terms:
        # 각 검색어별 상세 분석 (상위 20개까지)
        result = detailed_search_analysis(search_term, max_results=20)
        all_results[search_term] = result
        
        print("\n" + "="*80)
    
    # 결과 저장
    output_file = "results/spy_family_search_comparison.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"💾 비교 결과 저장: {output_file}")
    except Exception as e:
        print(f"❌ 저장 실패: {e}")
    
    # 비교 분석
    print("\n🔍 검색 결과 비교 분석:")
    print("="*80)
    
    for term in search_terms:
        data = all_results[term]
        if data["search_success"]:
            print(f"📊 '{term}': {data['total_results']}개 결과")
        else:
            print(f"❌ '{term}': 검색 실패")
    
    # SPY×FAMILY 관련 제목 찾기
    print(f"\n🎯 SPY×FAMILY 관련 제목 비교:")
    print("-" * 60)
    
    for term in search_terms:
        data = all_results[term]
        if data["search_success"]:
            print(f"\n📝 '{term}' 결과에서 SPY×FAMILY 관련:")
            spy_family_found = []
            
            for result in data["results"]:
                if "error" not in result:
                    title = result["name"]
                    if "SPY" in title.upper() and "FAMILY" in title.upper():
                        spy_family_found.append(f"#{result['rank']}: {title}")
            
            if spy_family_found:
                for item in spy_family_found:
                    print(f"   ✅ {item}")
            else:
                print("   ❌ SPY×FAMILY 관련 제목 없음")
    
    print(f"\n✅ 검색어 비교 분석 완료!")
    
    return all_results

if __name__ == "__main__":
    compare_spy_family_searches()
