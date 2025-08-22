# 라프텔 검색 결과 검증용 스크립트
# 검색어와 실제 매칭 결과를 비교하여 정확성 확인
import csv
import laftel
import json

INPUT_CSV = "anime.csv"
VALIDATION_OUTPUT = "search_validation.json"
VALIDATION_CSV = "search_validation.csv"

def validate_search_results(title: str, max_results: int = 5):
    """검색 결과를 검증하고 상세 정보 반환"""
    print(f"🔍 '{title}' 검색 결과 검증:")
    print("-" * 50)
    
    try:
        results = laftel.sync.searchAnime(title)
        if not results:
            print(f"❌ 검색 결과 없음")
            return {
                "search_query": title,
                "found_results": False,
                "result_count": 0,
                "candidates": []
            }
        
        print(f"✅ 총 {len(results)}개 결과 발견")
        
        candidates = []
        for i, result in enumerate(results[:max_results]):
            print(f"\n📺 결과 #{i+1}:")
            print(f"   제목: {result.name}")
            print(f"   ID: {result.id}")
            print(f"   장르: {result.genres}")
            
            # 상세 정보 가져오기
            try:
                info = laftel.sync.getAnimeInfo(result.id)
                episodes = laftel.sync.searchEpisodes(result.id)
                total_episodes = len(episodes) if episodes else 0
                
                candidate_info = {
                    "rank": i + 1,
                    "id": result.id,
                    "title": result.name,
                    "genres": result.genres,
                    "air_year_quarter": info.air_year_quarter or "",
                    "avg_rating": info.avg_rating or 0.0,
                    "status": "완결" if getattr(info, "ended", False) else "방영중",
                    "production": info.production or "",
                    "total_episodes": total_episodes,
                    "laftel_url": info.url or "",
                    "similarity_score": calculate_similarity(title, result.name)
                }
                
                candidates.append(candidate_info)
                
                print(f"   방영분기: {candidate_info['air_year_quarter']}")
                print(f"   평점: {candidate_info['avg_rating']}")
                print(f"   상태: {candidate_info['status']}")
                print(f"   제작사: {candidate_info['production']}")
                print(f"   총 화수: {candidate_info['total_episodes']}화")
                print(f"   유사도: {candidate_info['similarity_score']:.2f}")
                
            except Exception as e:
                print(f"   ❌ 상세 정보 가져오기 실패: {e}")
                candidates.append({
                    "rank": i + 1,
                    "id": result.id,
                    "title": result.name,
                    "genres": result.genres,
                    "error": str(e)
                })
        
        return {
            "search_query": title,
            "found_results": True,
            "result_count": len(results),
            "candidates": candidates,
            "recommended_choice": candidates[0] if candidates else None
        }
        
    except Exception as e:
        print(f"❌ 검색 오류: {e}")
        return {
            "search_query": title,
            "found_results": False,
            "result_count": 0,
            "error": str(e),
            "candidates": []
        }

def calculate_similarity(query: str, result_title: str):
    """간단한 문자열 유사도 계산 (0.0 ~ 1.0)"""
    query_clean = query.lower().replace(" ", "").replace(":", "").replace("-", "")
    result_clean = result_title.lower().replace(" ", "").replace(":", "").replace("-", "").replace("(", "").replace(")", "").replace("【", "").replace("】", "")
    
    # 포함 관계 확인
    if query_clean in result_clean or result_clean in query_clean:
        return 0.8
    
    # 단어별 매칭 확인
    query_words = set(query.lower().split())
    result_words = set(result_title.lower().split())
    
    if query_words and result_words:
        intersection = query_words & result_words
        union = query_words | result_words
        return len(intersection) / len(union)
    
    return 0.0

def main():
    print("🔍 라프텔 검색 결과 검증 시작!")
    print("=" * 70)
    
    all_validations = []
    validation_rows = []
    
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            query = (row.get("title") or "").strip()
            if not query:
                continue
                
            print(f"\n[{i+1}] 검증 중: {query}")
            validation_result = validate_search_results(query)
            all_validations.append(validation_result)
            
            # CSV 출력용 데이터 준비
            if validation_result["found_results"] and validation_result["candidates"]:
                best_match = validation_result["candidates"][0]
                validation_rows.append({
                    "search_query": query,
                    "matched_title": best_match["title"],
                    "similarity": best_match.get("similarity_score", 0),
                    "air_year_quarter": best_match.get("air_year_quarter", ""),
                    "avg_rating": best_match.get("avg_rating", 0),
                    "status": best_match.get("status", ""),
                    "production": best_match.get("production", ""),
                    "total_episodes": best_match.get("total_episodes", 0),
                    "laftel_url": best_match.get("laftel_url", ""),
                    "result_count": validation_result["result_count"],
                    "needs_review": "⚠️" if best_match.get("similarity_score", 0) < 0.7 else "✅"
                })
            else:
                validation_rows.append({
                    "search_query": query,
                    "matched_title": "❌ 검색 결과 없음",
                    "similarity": 0,
                    "needs_review": "❌"
                })
            
            print("=" * 70)
    
    # JSON 형태로 상세 결과 저장
    with open(VALIDATION_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(all_validations, f, ensure_ascii=False, indent=2)
    
    # CSV 형태로 요약 결과 저장
    if validation_rows:
        with open(VALIDATION_CSV, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["search_query", "matched_title", "similarity", "air_year_quarter", 
                         "avg_rating", "status", "production", "total_episodes", 
                         "laftel_url", "result_count", "needs_review"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(validation_rows)
    
    print(f"\n🎉 검증 완료!")
    print(f"📋 상세 결과: {VALIDATION_OUTPUT}")
    print(f"📊 요약 결과: {VALIDATION_CSV}")
    
    # 검토 필요한 항목 요약
    needs_review = [row for row in validation_rows if row["needs_review"] in ["⚠️", "❌"]]
    if needs_review:
        print(f"\n⚠️ 검토 필요한 항목 {len(needs_review)}개:")
        for item in needs_review:
            print(f"   - '{item['search_query']}' → '{item['matched_title']}'")
    else:
        print(f"\n✅ 모든 검색 결과가 적절합니다!")

if __name__ == "__main__":
    main()
