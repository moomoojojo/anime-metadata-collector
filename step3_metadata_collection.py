#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3단계: 선정된 애니메이션 메타데이터 수집

2단계에서 매칭된 애니메이션의 상세 메타데이터를 라프텔 API로 수집
"""

import json
import os
import laftel
from datetime import datetime
from typing import Dict, Any, Optional, List
import glob
import config

def load_latest_llm_result() -> Dict[str, Any]:
    """2단계에서 생성된 최신 LLM 매칭 결과 로드"""
    try:
        # results 디렉토리에서 llm_choice_*.json 또는 llm_choice.json 파일 찾기
        llm_files = glob.glob(os.path.join(config.RESULTS_DIR, "llm_choice*.json"))
        
        if not llm_files:
            print(f"❌ LLM 결과 파일을 찾을 수 없습니다: {config.RESULTS_DIR}/llm_choice*.json")
            return {}
        
        # 가장 최신 파일 선택
        latest_file = max(llm_files, key=os.path.getctime)
        print(f"📥 최신 LLM 결과 로드: {latest_file}")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    except Exception as e:
        print(f"❌ LLM 결과 로드 실패: {e}")
        return {}

def load_latest_search_result() -> Dict[str, Any]:
    """1단계에서 생성된 최신 검색 결과 로드"""
    try:
        # results 디렉토리에서 search_results_*.json 파일들 찾기
        search_files = glob.glob(os.path.join(config.RESULTS_DIR, "search_results_*.json"))
        
        if not search_files:
            print(f"❌ 검색 결과 파일을 찾을 수 없습니다")
            return {}
        
        # 가장 최신 파일 선택
        latest_file = max(search_files, key=os.path.getctime)
        print(f"📥 최신 검색 결과 로드: {latest_file}")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    except Exception as e:
        print(f"❌ 검색 결과 로드 실패: {e}")
        return {}

def find_anime_id_by_title(selected_title: str, user_input: str) -> Optional[int]:
    """선택된 제목으로 애니메이션 ID 찾기"""
    try:
        print(f"🔍 애니메이션 ID 검색 중...")
        print(f"   선택된 제목: {selected_title}")
        
        # 선택된 제목으로 다시 검색해서 정확한 ID 찾기
        search_results = laftel.sync.searchAnime(selected_title)
        
        if not search_results:
            print(f"❌ '{selected_title}'로 검색 결과가 없습니다.")
            return None
        
        # 정확히 일치하는 제목 찾기
        for result in search_results:
            if result.name == selected_title:
                print(f"✅ 정확한 매칭 발견: ID {result.id}")
                return result.id
        
        # 정확한 매칭이 없으면 첫 번째 결과 사용
        first_result = search_results[0]
        print(f"⚠️ 정확한 매칭 없음, 첫 번째 결과 사용: ID {first_result.id}")
        print(f"   첫 번째 결과: {first_result.name}")
        
        return first_result.id
        
    except Exception as e:
        print(f"❌ ID 검색 중 오류: {e}")
        return None

def fetch_detailed_metadata(anime_id: int) -> Dict[str, Any]:
    """애니메이션 ID로 상세 메타데이터 수집"""
    try:
        print(f"📊 상세 정보 수집 중... (ID: {anime_id})")
        
        # 애니메이션 상세 정보
        info = laftel.sync.getAnimeInfo(anime_id)
        print(f"✅ 기본 정보 수집 완료: {info.name}")
        
        # 에피소드 정보로 총 화수 계산
        print(f"🎬 에피소드 정보 조회 중...")
        try:
            episodes = laftel.sync.searchEpisodes(anime_id)
            total_episodes = len(episodes) if episodes else 0
            print(f"📺 총 {total_episodes}화 확인")
        except Exception as ep_error:
            print(f"⚠️ 에피소드 정보 조회 실패: {ep_error}")
            total_episodes = 0
        
        # 상태 판정
        status = "완결" if getattr(info, "ended", False) else "방영중"
        
        metadata = {
            "name": info.name or "",
            "air_year_quarter": info.air_year_quarter or "",
            "avg_rating": info.avg_rating or 0.0,
            "status": status,
            "laftel_url": info.url or "",
            "cover_url": info.image or "",
            "production": info.production if info.production is not None else "",
            "total_episodes": total_episodes
        }
        
        print(f"✅ 메타데이터 수집 완료!")
        print(f"   제목: {metadata['name']}")
        print(f"   방영분기: {metadata['air_year_quarter']}")
        print(f"   평점: {metadata['avg_rating']}")
        print(f"   상태: {metadata['status']}")
        print(f"   제작사: {metadata['production']}")
        print(f"   총 화수: {metadata['total_episodes']}화")
        
        return metadata
        
    except Exception as e:
        print(f"❌ 메타데이터 수집 실패: {e}")
        return {}

def collect_metadata() -> Dict[str, Any]:
    """3단계 메인 함수: 메타데이터 수집"""
    
    print(f"🎬 3단계: 메타데이터 수집 시작")
    print("="*80)
    
    # 2단계 결과 로드
    llm_result = load_latest_llm_result()
    if not llm_result:
        return {
            "metadata_success": False,
            "skip_reason": "2단계 결과를 로드할 수 없음",
            "timestamp": datetime.now().isoformat()
        }
    
    # 매칭 상태 확인
    match_status = llm_result.get("match_status")
    if match_status != "match_found":
        print(f"⏭️ 3단계 건너뛰기: 2단계에서 매칭되지 않음")
        print(f"   매칭 상태: {match_status}")
        print(f"   이유: {llm_result.get('reason', '알 수 없음')}")
        
        return {
            "metadata_success": False,
            "skip_reason": "2단계에서 매칭되지 않음",
            "llm_status": match_status,
            "llm_reason": llm_result.get("reason", ""),
            "user_input": llm_result.get("user_input", ""),
            "timestamp": datetime.now().isoformat()
        }
    
    # 매칭 성공한 경우 메타데이터 수집
    selected_title = llm_result["selected_title"]
    user_input = llm_result.get("user_input", "")
    confidence = llm_result.get("confidence", 0)
    
    print(f"✅ 2단계 매칭 성공 확인")
    print(f"   원본 입력: {user_input}")
    print(f"   선택된 제목: {selected_title}")
    print(f"   신뢰도: {confidence}%")
    
    # 애니메이션 ID 찾기
    anime_id = find_anime_id_by_title(selected_title, user_input)
    if not anime_id:
        return {
            "metadata_success": False,
            "error": "애니메이션 ID를 찾을 수 없음",
            "selected_title": selected_title,
            "user_input": user_input,
            "timestamp": datetime.now().isoformat()
        }
    
    # 상세 메타데이터 수집
    metadata = fetch_detailed_metadata(anime_id)
    if not metadata:
        return {
            "metadata_success": False,
            "error": "메타데이터 수집 실패",
            "anime_id": anime_id,
            "selected_title": selected_title,
            "user_input": user_input,
            "timestamp": datetime.now().isoformat()
        }
    
    # 결과 구성
    result = {
        "metadata_success": True,
        "user_input": user_input,
        "selected_title": selected_title,
        "anime_id": anime_id,
        "confidence": confidence,
        "metadata": metadata,
        "timestamp": datetime.now().isoformat()
    }
    
    return result

def save_metadata_results(results: Dict[str, Any]) -> None:
    """메타데이터 수집 결과를 JSON 파일로 저장"""
    try:
        os.makedirs(config.RESULTS_DIR, exist_ok=True)
        with open(config.METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"💾 메타데이터 결과 저장: {config.METADATA_FILE}")
    except Exception as e:
        print(f"❌ 저장 실패: {e}")

def main():
    """메인 실행 함수"""
    print("🚀 3단계 메타데이터 수집 실행")
    print("="*80)
    
    # 메타데이터 수집
    results = collect_metadata()
    
    # 결과 저장
    save_metadata_results(results)
    
    # 결과 요약
    print("\n" + "="*80)
    print("📊 3단계 결과 요약:")
    
    if results.get("metadata_success"):
        metadata = results["metadata"]
        print("✅ 메타데이터 수집 성공!")
        print(f"   📝 원본 입력: {results['user_input']}")
        print(f"   🎯 선택된 제목: {results['selected_title']}")
        print(f"   🆔 애니메이션 ID: {results['anime_id']}")
        print(f"   🔍 신뢰도: {results['confidence']}%")
        print(f"\n📋 수집된 메타데이터:")
        print(f"   제목: {metadata['name']}")
        print(f"   방영분기: {metadata['air_year_quarter']}")
        print(f"   평점: {metadata['avg_rating']}")
        print(f"   상태: {metadata['status']}")
        print(f"   라프텔 URL: {metadata['laftel_url']}")
        print(f"   제작사: {metadata['production']}")
        print(f"   총 화수: {metadata['total_episodes']}화")
        print(f"\n🎯 4단계 노션 업로드 준비 완료!")
        
    else:
        print("❌ 메타데이터 수집 실패 또는 건너뛰기")
        if "skip_reason" in results:
            print(f"   건너뛰기 이유: {results['skip_reason']}")
        if "error" in results:
            print(f"   오류: {results['error']}")

if __name__ == "__main__":
    main()
