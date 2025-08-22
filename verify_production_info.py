#!/usr/bin/env python3
"""
제작사 정보 검증 스크립트
라프텔 API에서 제작사 정보가 정말 없는지 다양한 방법으로 확인
"""

import laftel
import json

def analyze_anime_fields(anime_info, title="Unknown"):
    """애니메이션 객체의 모든 필드를 분석"""
    print(f"\n🎬 '{title}' 분석 결과:")
    print("="*60)
    
    # 기본 정보
    print(f"📝 제목: {anime_info.name}")
    print(f"🆔 ID: {anime_info.id}")
    
    # 제작사 관련 필드들 우선 확인
    production_fields = []
    studio_fields = []
    
    print(f"\n🏭 제작사 관련 필드 검색:")
    for attr in dir(anime_info):
        if not attr.startswith('_') and not callable(getattr(anime_info, attr)):
            try:
                value = getattr(anime_info, attr)
                attr_lower = attr.lower()
                
                # 제작사 관련 키워드 검색
                if any(keyword in attr_lower for keyword in ['production', 'studio', 'company', 'maker']):
                    production_fields.append((attr, value))
                    print(f"  🔍 {attr}: {value}")
                    
                # 값에서 스튜디오 관련 내용 검색 (값이 문자열인 경우)
                if isinstance(value, str) and value:
                    value_lower = value.lower()
                    if any(keyword in value_lower for keyword in ['studio', '스튜디오', '제작', 'production', 'animation']):
                        studio_fields.append((attr, value))
            except Exception as e:
                pass
    
    if not production_fields:
        print("  ❌ 제작사 관련 필드 없음")
    
    if studio_fields:
        print(f"\n🎨 스튜디오 키워드 포함 필드들:")
        for attr, value in studio_fields:
            print(f"  📺 {attr}: {value}")
    
    # 모든 필드 출력 (None이 아닌 것들만)
    print(f"\n📋 모든 유효 필드들:")
    valid_fields = []
    for attr in sorted(dir(anime_info)):
        if not attr.startswith('_') and not callable(getattr(anime_info, attr)):
            try:
                value = getattr(anime_info, attr)
                if value is not None and value != "":
                    valid_fields.append((attr, value))
                    print(f"  ✅ {attr}: {value}")
            except Exception as e:
                print(f"  ⚠️ {attr}: 오류 - {e}")
    
    return {
        "production_fields": production_fields,
        "studio_fields": studio_fields, 
        "all_valid_fields": valid_fields
    }

def search_and_analyze(search_term):
    """애니메이션 검색 후 분석"""
    print(f"\n🔍 '{search_term}' 검색 중...")
    
    try:
        # 검색
        search_results = laftel.sync.searchAnime(search_term)
        if not search_results:
            print(f"❌ '{search_term}' 검색 결과 없음")
            return None
            
        print(f"✅ {len(search_results)}개 검색 결과 발견")
        
        # 첫 번째 결과 분석
        first_result = search_results[0]
        print(f"🎯 첫 번째 결과: {first_result.name}")
        
        # 상세 정보 가져오기
        anime_info = laftel.sync.getAnimeInfo(first_result.id)
        analysis = analyze_anime_fields(anime_info, first_result.name)
        
        return {
            "search_term": search_term,
            "anime_info": {
                "id": anime_info.id,
                "name": anime_info.name
            },
            "analysis": analysis
        }
        
    except Exception as e:
        print(f"❌ '{search_term}' 분석 실패: {e}")
        return None

def main():
    """메인 검증 함수"""
    print("🏭 제작사 정보 검증 시작")
    print("="*80)
    
    # 검증 대상 목록 (필수 4개 + 추가 6개)
    test_cases = [
        # 필수 검증 대상 4개
        "Re : 제로부터 시작하는 이세계 생활 3기",
        "SPY×FAMILY part 1", 
        "귀멸의 칼날",
        "은혼",
        
        # 추가 검증 대상 6개 (다양한 장르와 시기)
        "진격의 거인",           # 인기 액션 애니메이션
        "원피스",               # 장기 연재 애니메이션  
        "나루토",               # 닌자 액션 애니메이션
        "데스노트",             # 심리 스릴러
        "강철의 연금술사",       # 판타지 액션
        "신세기 에반게리온"      # 로봇 애니메이션
    ]
    
    results = []
    
    for search_term in test_cases:
        result = search_and_analyze(search_term)
        if result:
            results.append(result)
    
    # 결과 요약
    print(f"\n🏁 검증 결과 요약")
    print("="*80)
    
    has_production_info = False
    for result in results:
        analysis = result["analysis"]
        production_count = len(analysis["production_fields"])
        studio_count = len(analysis["studio_fields"])
        
        print(f"\n🎬 {result['anime_info']['name']}")
        print(f"   📊 제작사 필드: {production_count}개")
        print(f"   🎨 스튜디오 키워드: {studio_count}개")
        
        if production_count > 0 or studio_count > 0:
            has_production_info = True
            print("   ✅ 제작사 정보 발견!")
            
            for field, value in analysis["production_fields"]:
                print(f"      🏭 {field}: {value}")
            for field, value in analysis["studio_fields"]:
                print(f"      🎨 {field}: {value}")
        else:
            print("   ❌ 제작사 정보 없음")
    
    # 최종 결론
    print(f"\n🏆 최종 결론:")
    if has_production_info:
        print("✅ 일부 애니메이션에서 제작사 정보를 찾을 수 있습니다!")
        print("💡 현재 코드를 개선할 수 있는 가능성이 있습니다.")
    else:
        print("❌ 모든 테스트 케이스에서 제작사 정보를 찾을 수 없습니다.")
        print("💭 라프텔 API의 한계로 보입니다.")
    
    # 결과를 JSON으로 저장
    with open('results/production_verification.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 상세 결과 저장: results/production_verification.json")

if __name__ == "__main__":
    main()
