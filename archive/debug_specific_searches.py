# 특정 검색 케이스들의 상세 분석
import laftel

def analyze_search_case(query: str, expected_keywords: list = None):
    """특정 검색어에 대한 상세 분석"""
    print(f"🔍 '{query}' 상세 검색 분석")
    print("=" * 80)
    
    try:
        results = laftel.sync.searchAnime(query)
        if not results:
            print("❌ 검색 결과 없음")
            return
            
        print(f"✅ 총 {len(results)}개 결과 발견")
        print(f"📋 상위 10개 결과 목록:")
        print("-" * 80)
        
        for i, result in enumerate(results[:10]):
            print(f"\n📺 결과 #{i+1}:")
            print(f"   ID: {result.id}")
            print(f"   제목: {result.name}")
            print(f"   장르: {result.genres}")
            print(f"   성인콘텐츠: {result.adultonly}")
            
            # 키워드 매칭 확인
            if expected_keywords:
                matched_keywords = []
                for keyword in expected_keywords:
                    if keyword.lower() in result.name.lower():
                        matched_keywords.append(keyword)
                print(f"   매칭 키워드: {matched_keywords if matched_keywords else '없음'}")
            
            # 상세 정보 확인
            try:
                info = laftel.sync.getAnimeInfo(result.id)
                episodes = laftel.sync.searchEpisodes(result.id)
                total_episodes = len(episodes) if episodes else 0
                
                print(f"   방영분기: {info.air_year_quarter or 'N/A'}")
                print(f"   평점: {info.avg_rating or 'N/A'}")
                print(f"   상태: {'완결' if getattr(info, 'ended', False) else '방영중'}")
                print(f"   제작사: {info.production or 'N/A'}")
                print(f"   총 화수: {total_episodes}화")
                print(f"   URL: {info.url}")
                
                # 특별한 타입 확인 (극장판, OVA 등)
                anime_type = "일반"
                if "극장판" in result.name or "movie" in result.name.lower():
                    anime_type = "극장판"
                elif "OVA" in result.name or "OAD" in result.name:
                    anime_type = "OVA/OAD"
                elif "스페셜" in result.name or "special" in result.name.lower():
                    anime_type = "스페셜"
                elif total_episodes == 1:
                    anime_type = "단편/스페셜"
                
                print(f"   타입: {anime_type}")
                
            except Exception as e:
                print(f"   ❌ 상세 정보 가져오기 실패: {e}")
            
            print("-" * 50)
            
    except Exception as e:
        print(f"❌ 검색 오류: {e}")

def main():
    # 1. 무직전생 케이스 분석
    print("🎯 케이스 1: 무직전생")
    analyze_search_case(
        "무직전생 ~이세계에 갔으면 최선을 다한다~ 1기",
        expected_keywords=["무직전생", "1기", "part1", "part 1", "시즌1"]
    )
    
    print("\n" + "="*100 + "\n")
    
    # 2. 스파이 패밀리 케이스 분석
    print("🎯 케이스 2: 스파이 패밀리")
    analyze_search_case(
        "스파이 패밀리 1기",
        expected_keywords=["스파이 패밀리", "1기", "시즌1", "part1"]
    )
    
    print("\n" + "="*100 + "\n")
    
    # 3. Re: 제로 케이스 분석
    print("🎯 케이스 3: Re: 제로부터 시작하는 이세계 생활")
    analyze_search_case(
        "Re: 제로부터 시작하는 이세계 생활 1기",
        expected_keywords=["Re", "제로", "1기", "시즌1", "part1"]
    )

if __name__ == "__main__":
    main()
