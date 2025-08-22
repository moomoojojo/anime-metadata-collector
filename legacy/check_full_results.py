# 라프텔 검색 결과 전체 개수 확인
import laftel

def check_full_search_results(query: str):
    """라프텔 검색 결과 전체 개수와 모든 제목 확인"""
    print(f"🔍 '{query}' 전체 검색 결과 확인")
    print("=" * 80)
    
    try:
        results = laftel.sync.searchAnime(query)
        
        if not results:
            print("❌ 검색 결과 없음")
            return
            
        print(f"✅ 총 검색 결과: {len(results)}개")
        print(f"📋 모든 검색 결과 제목:")
        print("-" * 80)
        
        for i, result in enumerate(results):
            print(f"{i+1:2d}. {result.name}")
            
    except Exception as e:
        print(f"❌ 오류: {e}")

def main():
    test_queries = [
        "무직전생 ~이세계에 갔으면 최선을 다한다~ 1기",
        "Re: 제로부터 시작하는 이세계 생활 3기"
    ]
    
    for query in test_queries:
        check_full_search_results(query)
        print("\n" + "="*100 + "\n")

if __name__ == "__main__":
    main()
