# 1단계: 라프텔 검색 결과 수집 및 저장
import json
import laftel
import re
from datetime import datetime
from typing import List, Dict, Any
from . import config

def optimize_search_term(user_input: str) -> str:
    """라프텔 검색 최적화를 위한 검색어 전처리"""
    
    # 시즌 정보 패턴들
    season_patterns = [
        r'\s*1기\s*$',          # "스파이 패밀리 1기" → "스파이 패밀리"
        r'\s*2기\s*$',          # "무직전생 2기" → "무직전생"  
        r'\s*3기\s*$',          # "애니 3기" → "애니"
        r'\s*4기\s*$',          # "애니 4기" → "애니"
        r'\s*5기\s*$',          # "애니 5기" → "애니"
        r'\s*시즌\s*\d+\s*$',   # "애니 시즌 2" → "애니"
        r'\s*Season\s*\d+\s*$', # "애니 Season 2" → "애니"
    ]
    
    # 패턴 매칭해서 시즌 정보 제거
    for pattern in season_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            return re.sub(pattern, '', user_input, flags=re.IGNORECASE).strip()
    
    return user_input

def collect_search_candidates(user_input: str) -> Dict[str, Any]:
    """
    사용자 입력으로 라프텔 검색을 수행하고 후보군을 수집 (전처리 적용)
    
    Args:
        user_input: 사용자가 입력한 애니메이션 제목
        
    Returns:
        검색 결과 및 후보 정보가 담긴 딕셔너리
    """
    
    # 검색어 전처리
    search_term = optimize_search_term(user_input)
    
    if search_term != user_input:
        print(f"🔧 검색어 전처리 적용:")
        print(f"   원본: {user_input}")
        print(f"   검색어: {search_term}")
    else:
        print(f"🔧 검색어 전처리 없음 (원본 그대로)")
    
    print(f"🔍 1단계: '{search_term}' 라프텔 검색 시작")
    print("=" * 60)
    
    try:
        # 라프텔 검색 수행 (전처리된 검색어 사용)
        search_results = laftel.sync.searchAnime(search_term)
        
        if not search_results:
            print("❌ 검색 결과가 없습니다.")
            return {
                "user_input": user_input,
                "search_term": search_term,
                "preprocessing_applied": search_term != user_input,
                "search_timestamp": datetime.now().isoformat(),
                "total_results": 0,
                "candidate_titles": [],
                "search_success": False,
                "error_message": "검색 결과 없음"
            }
        
        print(f"✅ 총 {len(search_results)}개 검색 결과 발견")
        print(f"📊 상위 {min(config.MAX_SEARCH_CANDIDATES, len(search_results))}개 후보 수집 중...")
        
        candidates = []
        
        # 상위 N개 후보의 제목만 수집 (비용 최소화)
        candidate_titles = []
        
        for i, result in enumerate(search_results[:config.MAX_SEARCH_CANDIDATES]):
            try:
                print(f"📺 후보 #{i+1}: {result.name}")
                candidate_titles.append(result.name)
                
            except Exception as e:
                print(f"❌ 후보 #{i+1} 수집 실패: {e}")
        
        candidates = candidate_titles
        
        result_data = {
            "user_input": user_input,
            "search_term": search_term,
            "preprocessing_applied": search_term != user_input,
            "search_timestamp": datetime.now().isoformat(),
            "total_results": len(search_results),
            "collected_candidates": len(candidates),
            "candidate_titles": candidates,
            "search_success": True
        }
        
        print(f"\n✅ 1단계 완료: {len(candidates)}개 후보 수집 성공")
        return result_data
        
    except Exception as e:
        print(f"❌ 검색 중 오류 발생: {e}")
        return {
            "user_input": user_input,
            "search_term": search_term,
            "preprocessing_applied": search_term != user_input,
            "search_timestamp": datetime.now().isoformat(),
            "total_results": 0,
            "candidate_titles": [],
            "search_success": False,
            "error_message": str(e)
        }

def save_search_results(results: Dict[str, Any]) -> None:
    """검색 결과를 JSON 파일로 저장"""
    try:
        with open(config.SEARCH_RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"💾 검색 결과 저장 완료: {config.SEARCH_RESULTS_FILE}")
    except Exception as e:
        print(f"❌ 저장 실패: {e}")

def main():
    """메인 실행 함수"""
    # CSV 파일에서 첫 번째 항목 읽기
    import csv
    
    try:
        with open('anime.csv', 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # 헤더 스킵
            first_anime = next(reader)[0]
        
        test_inputs = [first_anime]
        
    except Exception as e:
        print(f"❌ CSV 파일 읽기 실패: {e}")
        # 기본값으로 폴백
        test_inputs = ["SPY×FAMILY part 1"]
    
    print("🚀 1단계 테스트 시작")
    print("="*80)
    
    for user_input in test_inputs:
        print(f"\n🎯 테스트 입력: '{user_input}'")
        
        # 검색 결과 수집
        results = collect_search_candidates(user_input)
        
        # 결과 저장 (각 테스트마다 별도 파일로 저장)
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"results/search_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"💾 결과 저장: {filename}")
        except Exception as e:
            print(f"❌ 저장 실패: {e}")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    main()
