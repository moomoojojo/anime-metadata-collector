# 라프텔 검색 결과 디버깅 스크립트
import laftel
import json

def debug_search(title: str):
    """라프텔 검색 결과를 자세히 분석"""
    print(f"🔍 '{title}' 검색 결과 분석:")
    print("=" * 60)
    
    try:
        results = laftel.sync.searchAnime(title)
        
        if not results:
            print("❌ 검색 결과가 없습니다.")
            return
            
        print(f"✅ 총 {len(results)}개의 검색 결과 발견\n")
        
        # 상위 5개 결과만 확인
        for i, result in enumerate(results[:5]):
            print(f"📺 결과 #{i+1}:")
            print(f"   제목: {result.name}")
            print(f"   ID: {result.id}")
            print(f"   타입: {getattr(result, 'content_type', 'N/A')}")
            
            # 상세 정보 가져오기
            try:
                info = result.get_data()
                print(f"   정식 제목: {info.name}")
                print(f"   방영분기: {info.air_year_quarter or 'N/A'}")
                print(f"   평점: {info.avg_rating}")
                print(f"   상태: {'완결' if getattr(info, 'ended', False) else '방영중'}")
                print(f"   장르: {getattr(info, 'genres', 'N/A')}")
                print(f"   태그: {getattr(info, 'tags', 'N/A')}")
                print(f"   설명: {getattr(info, 'content', 'N/A')[:100]}...")
            except Exception as e:
                print(f"   ❌ 상세 정보 가져오기 실패: {e}")
            
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ 검색 중 오류 발생: {e}")

if __name__ == "__main__":
    test_titles = ["전생슬", "귀멸의 칼날", "카우보이 비밥", "원피스", "나루토"]
    
    for title in test_titles:
        debug_search(title)
        print("\n" + "="*80 + "\n")
