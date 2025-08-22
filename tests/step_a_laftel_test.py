# pip install laftel requests python-dotenv
import csv
import laftel

INPUT_CSV = "anime.csv"
OUTPUT_CSV = "anime_laftel_output.csv"

def fetch_one(title: str):
    """라프텔 검색 → 첫 결과 상세 → 8개 필수 필드 반환."""
    print(f"  검색 중: {title}")
    try:
        results = laftel.sync.searchAnime(title)      # 후보 목록
        if not results:
            print(f"  ❌ '{title}' 검색 결과가 없습니다.")
            return None

        print(f"  ✅ 검색 결과 {len(results)}개 발견")
        
        # 올바른 방법으로 상세 정보 가져오기
        first_result = results[0]
        info = laftel.sync.getAnimeInfo(first_result.id)
        print(f"  📊 상세 정보 가져오는 중...")
        
        # 에피소드 정보로 총 화수 계산
        print(f"  🎬 에피소드 정보 조회 중...")
        try:
            episodes = laftel.sync.searchEpisodes(first_result.id)
            total_episodes = len(episodes) if episodes else 0
            print(f"  📺 총 {total_episodes}화 확인")
        except Exception as ep_error:
            print(f"  ⚠️ 에피소드 정보 조회 실패: {ep_error}")
            total_episodes = 0
        
        return {
            "name": info.name,                                    # 1. 애니메이션 제목
            "air_year_quarter": info.air_year_quarter or "",      # 2. 방영분기
            "avg_rating": info.avg_rating or 0.0,                # 3. 라프텔 평점
            "status": "완결" if getattr(info, "ended", False) else "방영중",  # 4. 상태
            "laftel_url": info.url or "",                         # 5. 라프텔 URL
            "cover_url": info.image or "",                        # 6. 커버 URL
            "production": info.production or "",                  # 7. 제작사
            "total_episodes": total_episodes,                     # 8. 총 화수
        }
    except Exception as e:
        print(f"  ❌ 오류 발생: {e}")
        return None

def main():
    print("🎬 라프텔 API 테스트 시작!")
    print("=" * 50)
    
    rows_out = []
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            q = (row.get("title") or "").strip()
            if not q:
                continue
            print(f"\n🔍 [라프텔 검색] {q}")
            info = fetch_one(q)
            if not info:
                print("  → 결과 없음, 다음으로 넘어갑니다.")
                continue
            print(f"  → ✅ {info['name']}")
            print(f"     📅 방영분기: {info['air_year_quarter']}")
            print(f"     ⭐ 평점: {info['avg_rating']}")
            print(f"     📺 상태: {info['status']}")
            print(f"     🏭 제작사: {info['production']}")
            print(f"     🎬 총 화수: {info['total_episodes']}화")
            print(f"     🔗 URL: {info['laftel_url']}")
            rows_out.append(info)

    # 결과를 CSV로 저장(노션 업로드용 입력 파일)
    print("\n" + "=" * 50)
    if rows_out:
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as fw:
            fieldnames = ["name","air_year_quarter","avg_rating","status","laftel_url","cover_url","production","total_episodes"]
            w = csv.DictWriter(fw, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows_out)
        print(f"🎉 완료! {OUTPUT_CSV} 파일이 생성되었습니다.")
        print(f"📊 총 {len(rows_out)}개 작품의 정보를 수집했습니다.")
    else:
        print("❌ 저장할 결과가 없습니다.")
    
    print("\n다음 단계: python3 step_b_notion_upload.py 로 노션에 업로드하세요!")

if __name__ == "__main__":
    main()

