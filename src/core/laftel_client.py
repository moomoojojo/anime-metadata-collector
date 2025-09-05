# 🎯 라프텔 API 래퍼 클래스
"""
라프텔 비공식 API 래퍼 클래스
- 검색 기능과 메타데이터 수집 기능을 통합
- 에러 핸들링 및 재시도 로직 포함
- 기존 step1, step3 로직을 클래스로 래핑
"""

import laftel
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import time

from .models import SearchResult, SearchCandidate, MetadataResult, AnimeMetadata
from .config import settings

class LaftelClient:
    """라프텔 API 클라이언트"""
    
    def __init__(self):
        """클라이언트 초기화"""
        self.max_candidates = settings.max_search_candidates
        self.retry_count = 3
        self.retry_delay = 1.0  # 초
    
    def optimize_search_term(self, user_input: str) -> str:
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
    
    def search_anime(self, user_input: str) -> SearchResult:
        """
        애니메이션 검색
        
        Args:
            user_input: 사용자 입력 애니메이션 제목
            
        Returns:
            SearchResult: 검색 결과 객체
        """
        # 검색어 최적화
        search_query = self.optimize_search_term(user_input)
        
        try:
            print(f"🔧 검색어 전처리 적용:")
            print(f"   원본: {user_input}")
            print(f"   검색어: {search_query}")
            
            # 라프텔 검색 실행
            print(f"🔍 1단계: '{search_query}' 라프텔 검색 시작")
            print("=" * 60)
            
            # 재시도 로직 포함 검색
            search_results = None
            for attempt in range(self.retry_count):
                try:
                    search_results = laftel.sync.searchAnime(search_query)
                    break
                except Exception as e:
                    print(f"⚠️ 검색 시도 {attempt + 1} 실패: {e}")
                    if attempt < self.retry_count - 1:
                        time.sleep(self.retry_delay)
                        continue
                    raise
            
            if not search_results:
                return SearchResult(
                    user_input=user_input,
                    search_query=search_query,
                    candidates=[],
                    total_found=0,
                    success=False,
                    error_message="검색 결과가 없습니다."
                )
            
            total_found = len(search_results)
            print(f"✅ 총 {total_found}개 검색 결과 발견")
            
            # 상위 N개 후보 수집
            max_collect = min(self.max_candidates, total_found)
            print(f"📊 상위 {max_collect}개 후보 수집 중...")
            
            candidates = []
            for i, item in enumerate(search_results[:max_collect]):
                try:
                    candidate = SearchCandidate(
                        title=item.name,
                        laftel_id=str(item.id) if hasattr(item, 'id') else None,
                        rank=i + 1
                    )
                    candidates.append(candidate)
                    print(f"📺 후보 #{i + 1}: {item.name}")
                    
                except Exception as e:
                    print(f"⚠️ 후보 #{i + 1} 처리 실패: {e}")
                    continue
            
            return SearchResult(
                user_input=user_input,
                search_query=search_query,
                candidates=candidates,
                total_found=total_found,
                success=True
            )
            
        except Exception as e:
            error_msg = f"라프텔 검색 실패: {str(e)}"
            print(f"❌ {error_msg}")
            
            return SearchResult(
                user_input=user_input,
                search_query=search_query,
                candidates=[],
                total_found=0,
                success=False,
                error_message=error_msg
            )
    
    def get_anime_by_name(self, anime_name: str) -> Optional[Any]:
        """애니메이션 이름으로 정확한 객체 찾기"""
        try:
            search_results = laftel.sync.searchAnime(anime_name)
            
            # 정확한 매칭 찾기
            for item in search_results:
                if item.name == anime_name:
                    return item
            
            # 정확한 매칭이 없으면 첫 번째 결과 반환
            if search_results:
                return search_results[0]
                
            return None
            
        except Exception as e:
            print(f"❌ 애니메이션 검색 실패: {e}")
            return None
    
    def get_metadata(self, selected_title: str) -> MetadataResult:
        """
        선택된 애니메이션의 메타데이터 수집
        
        Args:
            selected_title: 선택된 애니메이션 제목
            
        Returns:
            MetadataResult: 메타데이터 수집 결과
        """
        try:
            print(f"🔍 애니메이션 ID 검색 중...")
            print(f"   선택된 제목: {selected_title}")
            
            # 애니메이션 객체 검색
            anime_obj = self.get_anime_by_name(selected_title)
            
            if not anime_obj:
                return MetadataResult(
                    selected_title=selected_title,
                    success=False,
                    error_message="애니메이션을 찾을 수 없습니다."
                )
            
            anime_id = anime_obj.id
            print(f"✅ 정확한 매칭 발견: ID {anime_id}")
            
            # 상세 정보 수집
            print(f"📊 상세 정보 수집 중... (ID: {anime_id})")
            
            # 재시도 로직 포함 메타데이터 수집
            for attempt in range(self.retry_count):
                try:
                    # 상세 정보 재조회 (laftel API 사용)
                    info = laftel.sync.getAnimeInfo(anime_id)
                    
                    name = info.name
                    air_year_quarter = getattr(info, 'air_year_quarter', None)
                    avg_rating = getattr(info, 'avg_rating', None)
                    status = getattr(info, 'status', None)
                    laftel_url = f"https://laftel.net/item/{anime_id}"
                    cover_url = getattr(info, 'image', None)  # 수정: img → image
                    production = getattr(info, 'production', None)
                    
                    print(f"✅ 기본 정보 수집 완료: {name}")
                    
                    # 에피소드 정보
                    total_episodes = None
                    try:
                        print(f"🎬 에피소드 정보 조회 중...")
                        episodes = laftel.sync.searchEpisodes(anime_id)
                        if episodes:
                            total_episodes = len(episodes)
                            print(f"📺 총 {total_episodes}화 확인")
                    except Exception as e:
                        print(f"⚠️ 에피소드 정보 수집 실패: {e}")
                    
                    # 메타데이터 객체 생성
                    metadata = AnimeMetadata(
                        laftel_id=str(anime_id),
                        name=name,
                        air_year_quarter=air_year_quarter,
                        avg_rating=float(avg_rating) if avg_rating else None,
                        status=status,
                        laftel_url=laftel_url,
                        cover_url=cover_url,
                        production=production,
                        total_episodes=total_episodes
                    )
                    
                    print(f"✅ 메타데이터 수집 완료!")
                    print(f"   제목: {metadata.name}")
                    print(f"   방영분기: {metadata.air_year_quarter}")
                    print(f"   평점: {metadata.avg_rating}")
                    print(f"   상태: {metadata.status}")
                    print(f"   제작사: {metadata.production}")
                    print(f"   총 화수: {metadata.total_episodes}화")
                    
                    return MetadataResult(
                        selected_title=selected_title,
                        metadata=metadata,
                        success=True
                    )
                    
                except Exception as e:
                    print(f"⚠️ 메타데이터 수집 시도 {attempt + 1} 실패: {e}")
                    if attempt < self.retry_count - 1:
                        time.sleep(self.retry_delay)
                        continue
                    raise
                    
        except Exception as e:
            error_msg = f"메타데이터 수집 실패: {str(e)}"
            print(f"❌ {error_msg}")
            
            return MetadataResult(
                selected_title=selected_title,
                success=False,
                error_message=error_msg
            )
