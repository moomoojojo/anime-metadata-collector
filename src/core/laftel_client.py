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
import requests
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import time
from urllib.parse import quote
import os

from .models import SearchResult, SearchCandidate, MetadataResult, AnimeMetadata
from .config import settings

# 렌더 환경에서는 CloudScraper 사용
try:
    from cloudscraper import create_scraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False

class LaftelClient:
    """라프텔 API 클라이언트"""
    
    def __init__(self):
        """클라이언트 초기화"""
        self.max_candidates = settings.max_search_candidates
        self.retry_count = 3
        self.retry_delay = 1.0  # 초
        
        # 렌더 환경 감지 및 HTTP 클라이언트 설정
        self.is_render_env = os.getenv('RENDER', '').lower() == 'true'
        if self.is_render_env and CLOUDSCRAPER_AVAILABLE:
            self.http_client = create_scraper()
            print("🌐 렌더 환경 감지: CloudScraper 사용")
        else:
            self.http_client = requests
            print("🏠 로컬 환경: requests 사용")
    
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
    
    def _get_laftel_headers(self) -> Dict[str, str]:
        """라프텔 API 호출용 헤더"""
        return {
            'Host': 'laftel.net',
            'laftel': 'TeJava',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_1_4; like Mac OS X) AppleWebKit/600.11 (KHTML, like Gecko)  Chrome/54.0.1486.383 Mobile Safari/600.8',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate'
        }
    
    def _direct_search_anime(self, query: str) -> List[Any]:
        """직접 HTTP 요청으로 라프텔 검색 (이벤트 루프 충돌 방지)"""
        encoded_query = quote(query)
        
        # 렌더 환경에서는 NCP 프록시 사용
        if self.is_render_env:
            # NCP 프록시를 통한 라프텔 API 호출
            proxy_url = f'http://49.50.135.81/laftel/api/search/v3/keyword/?keyword={encoded_query}'
            print(f"🌐 NCP 프록시를 통한 라프텔 검색: {proxy_url}")
        else:
            # 로컬에서는 직접 호출
            proxy_url = f'https://laftel.net/api/search/v3/keyword/?keyword={encoded_query}'
            print(f"🏠 직접 라프텔 검색: {proxy_url}")
        
        response = requests.get(proxy_url, headers=self._get_laftel_headers(), timeout=10)
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")
        
        try:
            data = response.json()
            # 라프텔 API 응답에서 실제 검색 결과 배열 추출
            if isinstance(data, dict) and 'results' in data:
                return data['results']
            else:
                return data
        except json.JSONDecodeError as e:
            raise Exception(f"JSON 파싱 실패: {e}")
    
    def _direct_get_anime_info(self, anime_id: int) -> Dict[str, Any]:
        """직접 HTTP 요청으로 라프텔 애니메이션 정보 조회"""
        # 렌더 환경에서는 NCP 프록시 사용
        if self.is_render_env:
            url = f'http://49.50.135.81/laftel/api/items/v3/{anime_id}/'
            print(f"🌐 NCP 프록시를 통한 애니메이션 정보 조회: {url}")
        else:
            url = f'https://laftel.net/api/items/v3/{anime_id}/'
            print(f"🏠 직접 애니메이션 정보 조회: {url}")
        
        response = requests.get(url, headers=self._get_laftel_headers(), timeout=10)
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")
        
        try:
            return response.json()
        except json.JSONDecodeError as e:
            raise Exception(f"JSON 파싱 실패: {e}")
    
    def _direct_get_episodes(self, anime_id: int) -> List[Dict[str, Any]]:
        """직접 HTTP 요청으로 라프텔 에피소드 정보 조회"""
        # 렌더 환경에서는 NCP 프록시 사용
        if self.is_render_env:
            url = f'http://49.50.135.81/laftel/api/episodes/v2/?item={anime_id}'
            print(f"🌐 NCP 프록시를 통한 에피소드 정보 조회: {url}")
        else:
            url = f'https://laftel.net/api/episodes/v2/?item={anime_id}'
            print(f"🏠 직접 에피소드 정보 조회: {url}")
        
        response = requests.get(url, headers=self._get_laftel_headers(), timeout=10)
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")
        
        try:
            return response.json()
        except json.JSONDecodeError as e:
            raise Exception(f"JSON 파싱 실패: {e}")
    
    def _extract_status(self, info: Dict[str, Any]) -> str:
        """라프텔 API 응답에서 방영 상태 추출"""
        try:
            # is_ending: 완결 여부
            if info.get('is_ending', False):
                return "완결"
            
            # is_upcoming_release: 방영 예정
            if info.get('is_upcoming_release', False):
                return "방영 예정"
            
            # is_new_release: 신작
            if info.get('is_new_release', False):
                return "방영 중"
                
            # latest_episode_release_datetime이 최근이면 방영 중
            latest_episode = info.get('latest_episode_release_datetime')
            if latest_episode:
                from datetime import datetime, timedelta
                try:
                    latest_date = datetime.fromisoformat(latest_episode.replace('Z', '+00:00'))
                    now = datetime.now(latest_date.tzinfo)
                    if (now - latest_date).days < 30:  # 30일 이내면 방영 중
                        return "방영 중"
                except:
                    pass
            
            # 기본값
            return "완결"
            
        except Exception as e:
            print(f"⚠️ 상태 추출 실패: {e}")
            return "알 수 없음"
    
    def _extract_cover_image(self, info: Dict[str, Any]) -> Optional[str]:
        """라프텔 API 응답에서 표지 이미지 URL 추출"""
        try:
            # 1순위: 직접 img 필드
            if info.get('img'):
                return info['img']
            
            # 2순위: images 배열에서 home_default 이미지
            images = info.get('images', [])
            if images:
                for image in images:
                    if image.get('option_name') == 'home_default':
                        return image.get('img_url')
                
                # 첫 번째 이미지라도
                if images[0].get('img_url'):
                    return images[0]['img_url']
            
            # 3순위: image 필드 (혹시 있다면)
            if info.get('image'):
                return info['image']
                
            return None
            
        except Exception as e:
            print(f"⚠️ 표지 이미지 추출 실패: {e}")
            return None
    
    def _extract_total_episodes(self, info: Dict[str, Any], anime_id: int) -> Optional[int]:
        """총 화수 정보 추출 (여러 방법 시도)"""
        try:
            # 1순위: API 응답에 직접 총 화수 정보가 있는지 확인
            if info.get('total_episodes'):
                print(f"📺 API에서 총 화수 발견: {info['total_episodes']}화")
                return info['total_episodes']
            
            if info.get('episode_count'):
                print(f"📺 API에서 화수 정보 발견: {info['episode_count']}화")
                return info['episode_count']
            
            # 2순위: 에피소드 API 시도
            try:
                print(f"🎬 에피소드 API 조회 중...")
                episodes = self._direct_get_episodes(anime_id)
                if episodes:
                    total = len(episodes)
                    print(f"📺 에피소드 API에서 총 {total}화 확인")
                    return total
            except Exception as e:
                print(f"⚠️ 에피소드 API 실패: {str(e)[:100]}...")
            
            # 3순위: 태그나 설명에서 화수 정보 추출
            tags = info.get('tags', [])
            for tag in tags:
                if isinstance(tag, str) and ('화' in tag or '편' in tag):
                    import re
                    numbers = re.findall(r'(\d+)(?:화|편)', tag)
                    if numbers:
                        episode_count = int(numbers[0])
                        print(f"📺 태그에서 화수 추출: {episode_count}화 (태그: {tag})")
                        return episode_count
            
            # 4순위: 기본값 또는 추정
            medium = info.get('medium', '')
            if medium == 'TVA':  # TV 애니메이션
                # is_ending이 true이고 recent하면 12화 정도로 추정
                if info.get('is_ending', False):
                    print(f"📺 TV 애니메이션 완결작 추정: 12화")
                    return 12
                    
            print(f"⚠️ 총 화수 정보를 찾을 수 없음")
            return None
            
        except Exception as e:
            print(f"⚠️ 총 화수 추출 실패: {e}")
            return None
    
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
            
            # 직접 HTTP 요청으로 라프텔 API 호출 (이벤트 루프 충돌 방지)
            search_results = None
            for attempt in range(self.retry_count):
                try:
                    search_results = self._direct_search_anime(search_query)
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
                    # 직접 HTTP 응답 데이터 처리
                    if isinstance(item, dict):
                        title = item.get('name', '')
                        laftel_id = str(item.get('id', ''))
                    else:
                        # 기존 laftel 객체 형태 (폴백)
                        title = item.name if hasattr(item, 'name') else str(item)
                        laftel_id = str(item.id) if hasattr(item, 'id') else None
                    
                    candidate = SearchCandidate(
                        title=title,
                        laftel_id=laftel_id,
                        rank=i + 1
                    )
                    candidates.append(candidate)
                    print(f"📺 후보 #{i + 1}: {title}")
                    
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
    
    def get_anime_by_name(self, anime_name: str) -> Optional[Dict[str, Any]]:
        """애니메이션 이름으로 정확한 객체 찾기 (직접 HTTP 요청 사용)"""
        try:
            search_results = self._direct_search_anime(anime_name)
            
            # 정확한 매칭 찾기
            for item in search_results:
                if isinstance(item, dict) and item.get('name') == anime_name:
                    return item
            
            # 정확한 매칭이 없으면 첫 번째 결과 반환
            if search_results and len(search_results) > 0:
                return search_results[0] if isinstance(search_results[0], dict) else None
                
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
            
            anime_id = anime_obj.get('id')
            if not anime_id:
                return MetadataResult(
                    selected_title=selected_title,
                    success=False,
                    error_message="애니메이션 ID를 찾을 수 없습니다."
                )
            
            print(f"✅ 정확한 매칭 발견: ID {anime_id}")
            
            # 상세 정보 수집
            print(f"📊 상세 정보 수집 중... (ID: {anime_id})")
            
            # 재시도 로직 포함 메타데이터 수집
            for attempt in range(self.retry_count):
                try:
                    # 상세 정보 재조회 (직접 HTTP 요청 사용)
                    info = self._direct_get_anime_info(anime_id)
                    
                    name = info.get('name', selected_title)
                    air_year_quarter = info.get('air_year_quarter')
                    avg_rating = info.get('avg_rating')
                    
                    # 방영 상태 추출 (is_ending, is_upcoming_release 등을 기반으로)
                    status = self._extract_status(info)
                    
                    laftel_url = f"https://laftel.net/item/{anime_id}"
                    
                    # 표지 이미지 추출 (여러 소스에서 시도)
                    cover_url = self._extract_cover_image(info)
                    
                    production = info.get('production')
                    
                    print(f"✅ 기본 정보 수집 완료: {name}")
                    
                    # 에피소드 정보 (여러 방법으로 시도)
                    total_episodes = self._extract_total_episodes(info, anime_id)
                    
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
