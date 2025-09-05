# 🎯 노션 API 래퍼 클래스
"""
노션 API 래퍼 클래스
- 페이지 생성 및 업데이트 기능
- 에러 핸들링 및 재시도 로직 포함
- 기존 step4 로직을 클래스로 래핑
"""

import requests
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from .models import NotionResult, AnimeMetadata
from .config import settings, NOTION_FIELD_MAPPING, NOTION_DEFAULT_VALUES

class NotionClient:
    """노션 API 클라이언트"""
    
    def __init__(self):
        """클라이언트 초기화"""
        self.token = settings.notion_token
        self.database_id = settings.notion_database_id
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        self.retry_count = 3
        self.retry_delay = 2.0  # 초
    
    def _validate_setup(self) -> bool:
        """설정 유효성 검사"""
        if not settings.notion_token:
            print("❌ 노션 API 토큰이 설정되지 않았습니다.")
            return False
            
        if not settings.notion_database_id:
            print("❌ 노션 데이터베이스 ID가 설정되지 않았습니다.")
            return False
            
        return True
    
    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """노션 API 요청 실행 (재시도 로직 포함)"""
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(self.retry_count):
            try:
                if method.upper() == "GET":
                    response = requests.get(url, headers=self.headers)
                elif method.upper() == "POST":
                    response = requests.post(url, headers=self.headers, json=data)
                elif method.upper() == "PATCH":
                    response = requests.patch(url, headers=self.headers, json=data)
                else:
                    raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")
                
                # 응답 확인
                if response.status_code in [200, 201]:
                    return response.json()
                elif response.status_code == 429:  # Rate limit
                    print(f"⚠️ 요청 한도 초과, {self.retry_delay}초 대기...")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    error_msg = f"API 요청 실패 (상태코드: {response.status_code})"
                    try:
                        error_detail = response.json()
                        error_msg += f": {error_detail.get('message', '알 수 없는 오류')}"
                    except:
                        error_msg += f": {response.text}"
                    raise Exception(error_msg)
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠️ 네트워크 오류 시도 {attempt + 1}: {e}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise
        
        raise Exception(f"API 요청 {self.retry_count}회 실패")
    
    def _create_page_properties(self, metadata: Optional[AnimeMetadata], 
                              user_input: str, is_new_page: bool = False) -> Dict[str, Any]:
        """메타데이터를 노션 페이지 속성으로 변환"""
        properties = {}
        
        # 제목 (Title) - 항상 필요
        properties["이름"] = {
            "title": [{"text": {"content": user_input}}]
        }
        
        # 메타데이터가 있는 경우에만 추가 속성 설정
        if metadata:
            # 라프텔 제목
            if metadata.name:
                properties["라프텔 제목"] = {
                    "rich_text": [{"text": {"content": metadata.name}}]
                }
            
            # 방영 분기
            if metadata.air_year_quarter:
                properties["방영 분기"] = {
                    "multi_select": [{"name": metadata.air_year_quarter}]
                }
            
            # 라프텔 평점
            if metadata.avg_rating:
                properties["라프텔 평점"] = {
                    "number": float(metadata.avg_rating)
                }
            
            # 방영 상태
            if metadata.status:
                properties["방영 상태"] = {
                    "select": {"name": metadata.status}
                }
            
            # 라프텔 URL
            if metadata.laftel_url:
                properties["라프텔 URL"] = {
                    "url": metadata.laftel_url
                }
            
            # 표지 이미지
            if metadata.cover_url:
                properties["표지"] = {
                    "url": metadata.cover_url
                }
            
            # 제작사
            if metadata.production:
                properties["제작사"] = {
                    "select": {"name": metadata.production}
                }
            
            # 총 화수
            if metadata.total_episodes:
                properties["총 화수"] = {
                    "number": metadata.total_episodes
                }
        
        # 신규 페이지인 경우 기본값 추가
        if is_new_page:
            for field_name, default_config in NOTION_DEFAULT_VALUES.items():
                if field_name not in properties:
                    field_type = default_config["type"]
                    value = default_config["value"]
                    
                    if field_type == "status":
                        properties[field_name] = {"status": {"name": value}}
                    elif field_type == "select":
                        properties[field_name] = {"select": {"name": value}}
                    elif field_type == "number":
                        properties[field_name] = {"number": value}
        
        return properties
    
    def find_existing_page(self, user_input: str) -> Optional[str]:
        """제목으로 기존 페이지 검색"""
        try:
            query_data = {
                "filter": {
                    "property": "이름",
                    "title": {
                        "equals": user_input
                    }
                }
            }
            
            response = self._make_request(
                "POST", 
                f"databases/{self.database_id}/query",
                query_data
            )
            
            results = response.get("results", [])
            if results:
                return results[0]["id"]
            
            return None
            
        except Exception as e:
            print(f"⚠️ 기존 페이지 검색 실패: {e}")
            return None
    
    def create_or_update_page(self, user_input: str, 
                            metadata: Optional[AnimeMetadata] = None) -> NotionResult:
        """
        노션 페이지 생성 또는 업데이트
        
        Args:
            user_input: 사용자가 입력한 애니메이션 제목
            metadata: 수집된 메타데이터 (없으면 기본 페이지만 생성)
            
        Returns:
            NotionResult: 노션 작업 결과
        """
        if not self._validate_setup():
            return NotionResult(
                success=False,
                error_message="노션 API 설정이 올바르지 않습니다."
            )
        
        try:
            print("📝 Step 4: 노션 업로드")
            
            # 기존 페이지 확인
            existing_page_id = self.find_existing_page(user_input)
            
            if existing_page_id:
                print(f"🔍 기존 페이지 발견: {user_input}")
                return self._update_existing_page(existing_page_id, user_input, metadata)
            else:
                print(f"📄 새 페이지 생성: {user_input}")
                return self._create_new_page(user_input, metadata)
                
        except Exception as e:
            error_msg = f"노션 작업 실패: {str(e)}"
            print(f"❌ {error_msg}")
            
            return NotionResult(
                success=False,
                error_message=error_msg
            )
    
    def _create_new_page(self, user_input: str, 
                        metadata: Optional[AnimeMetadata]) -> NotionResult:
        """새 노션 페이지 생성"""
        try:
            print("🚀 노션 페이지 생성 중...")
            
            properties = self._create_page_properties(metadata, user_input, is_new_page=True)
            
            page_data = {
                "parent": {"database_id": self.database_id},
                "properties": properties
            }
            
            if metadata and metadata.name:
                print(f"📝 제목: {metadata.name}")
            
            response = self._make_request("POST", "pages", page_data)
            
            page_id = response["id"]
            page_url = response["url"]
            
            print("✅ 노션 페이지 생성 성공!")
            print(f"📄 페이지 ID: {page_id}")
            print(f"🔗 페이지 URL: {page_url}")
            
            return NotionResult(
                page_id=page_id,
                page_url=page_url,
                is_new_page=True,
                updated_properties=properties,
                success=True
            )
            
        except Exception as e:
            raise Exception(f"페이지 생성 실패: {str(e)}")
    
    def _update_existing_page(self, page_id: str, user_input: str,
                            metadata: Optional[AnimeMetadata]) -> NotionResult:
        """기존 노션 페이지 업데이트"""
        try:
            print("🚀 노션 페이지 업데이트 중...")
            
            properties = self._create_page_properties(metadata, user_input, is_new_page=False)
            
            update_data = {
                "properties": properties
            }
            
            if metadata and metadata.name:
                print(f"📝 제목: {metadata.name}")
            
            response = self._make_request("PATCH", f"pages/{page_id}", update_data)
            
            page_url = response["url"]
            
            print("✅ 노션 페이지 업데이트 성공!")
            print(f"📄 페이지 ID: {page_id}")
            print(f"🔗 페이지 URL: {page_url}")
            
            return NotionResult(
                page_id=page_id,
                page_url=page_url,
                is_new_page=False,
                updated_properties=properties,
                success=True
            )
            
        except Exception as e:
            raise Exception(f"페이지 업데이트 실패: {str(e)}")
    
    def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """페이지 정보 조회"""
        try:
            response = self._make_request("GET", f"pages/{page_id}")
            return response
        except Exception as e:
            print(f"⚠️ 페이지 조회 실패: {e}")
            return None
    
    def query_database(self, filter_data: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """데이터베이스 쿼리"""
        try:
            query_data = {}
            if filter_data:
                query_data["filter"] = filter_data
            
            response = self._make_request(
                "POST", 
                f"databases/{self.database_id}/query",
                query_data
            )
            
            return response.get("results", [])
            
        except Exception as e:
            print(f"⚠️ 데이터베이스 쿼리 실패: {e}")
            return []
