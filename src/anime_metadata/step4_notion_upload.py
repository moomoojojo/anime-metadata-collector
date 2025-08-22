#!/usr/bin/env python3
"""
4단계: 노션 페이지 생성
3단계에서 수집한 메타데이터를 노션 데이터베이스에 페이지로 생성
"""

import json
import os
import requests
from datetime import datetime
from typing import Dict, Any, Optional
import glob
from dotenv import load_dotenv
from . import config

# 환경변수 로드
load_dotenv()

def load_metadata_results() -> Optional[Dict[str, Any]]:
    """3단계에서 생성한 메타데이터 결과 파일을 로드"""
    # 우선 timestamped 파일들을 찾아보기
    metadata_files = glob.glob("results/metadata_results_*.json")
    
    # timestamped 파일이 없으면 기본 파일 확인
    if not metadata_files:
        default_file = "results/metadata.json"
        if os.path.exists(default_file):
            metadata_files = [default_file]
    
    if not metadata_files:
        print("❌ 메타데이터 결과 파일을 찾을 수 없습니다.")
        return None
    
    # 가장 최신 파일 선택
    latest_file = max(metadata_files, key=os.path.getctime)
    print(f"📂 메타데이터 파일 로드: {latest_file}")
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 메타데이터 파일 로드 실패: {e}")
        return None

def create_notion_page_properties(metadata: Dict[str, Any], user_input: str, is_new_page: bool = False) -> Dict[str, Any]:
    """메타데이터를 노션 페이지 속성으로 변환"""
    properties = {}
    
    # 필수 필드들을 노션 형식으로 변환
    field_mapping = config.NOTION_FIELD_MAPPING
    
    # 이름 (Title) - 사용자 입력 제목을 노션 제목 칼럼에
    if "이름" in field_mapping:
        properties["이름"] = {
            "title": [{"text": {"content": user_input}}]
        }
    
    # 라프텔 제목 (Rich Text) - 라프텔에서 매칭된 제목
    if "라프텔 제목" in field_mapping and metadata and "name" in metadata:
        properties["라프텔 제목"] = {
            "rich_text": [{"text": {"content": metadata["name"]}}]
        }
    
    # 방영 분기 (Multi-select)
    if "방영 분기" in field_mapping and metadata and "air_year_quarter" in metadata and metadata["air_year_quarter"]:
        # "|"로 구분된 여러 분기를 분리하여 다중 선택으로 처리
        quarters = metadata["air_year_quarter"].split("|")
        properties["방영 분기"] = {
            "multi_select": [{"name": quarter.strip()} for quarter in quarters if quarter.strip()]
        }
    
    # 라프텔 평점 (Number)
    if "라프텔 평점" in field_mapping and metadata and "avg_rating" in metadata:
        properties["라프텔 평점"] = {
            "number": metadata["avg_rating"]
        }
    
    # 방영 상태 (Select)
    if "방영 상태" in field_mapping and metadata and "status" in metadata:
        properties["방영 상태"] = {
            "select": {"name": metadata["status"]}
        }
    
    # 라프텔 URL (URL)
    if "라프텔 URL" in field_mapping and metadata and "laftel_url" in metadata:
        properties["라프텔 URL"] = {
            "url": metadata["laftel_url"]
        }
    
    # 표지 (Files & Media)
    if "표지" in field_mapping and metadata and "cover_url" in metadata:
        properties["표지"] = {
            "files": [
                {
                    "type": "external",
                    "name": "Cover Image",
                    "external": {
                        "url": metadata["cover_url"]
                    }
                }
            ]
        }
    
    # 제작사 (Select) - 빈 값이면 스킵
    if "제작사" in field_mapping and metadata and "production" in metadata and metadata["production"].strip():
        properties["제작사"] = {
            "select": {"name": metadata["production"]}
        }
    
    # 총 화수 (Number)
    if "총 화수" in field_mapping and metadata and "total_episodes" in metadata:
        properties["총 화수"] = {
            "number": metadata["total_episodes"]
        }
    
    # 신규 페이지 생성 시 기본값 설정
    if is_new_page:
        default_values = config.NOTION_DEFAULT_VALUES
        for field_name, field_config in default_values.items():
            if field_name not in properties:  # 기존 값이 없을 때만 기본값 설정
                field_type = field_config["type"]
                field_value = field_config["value"]
                
                if field_type == "status":
                    properties[field_name] = {
                        "status": {"name": field_value}
                    }
                elif field_type == "select":
                    properties[field_name] = {
                        "select": {"name": field_value}
                    }
                elif field_type == "number":
                    properties[field_name] = {
                        "number": field_value
                    }
    
    return properties

def search_existing_page(user_input: str, headers: Dict[str, str], database_id: str) -> Optional[str]:
    """노션 데이터베이스에서 기존 애니메이션 페이지 검색"""
    query_payload = {
        "filter": {
            "and": [
                {
                    "property": "이름",
                    "title": {
                        "equals": user_input
                    }
                },
                {
                    "property": "분류",
                    "select": {
                        "equals": "애니메이션"
                    }
                }
            ]
        }
    }
    
    try:
        response = requests.post(
            f"https://api.notion.com/v1/databases/{database_id}/query",
            headers=headers,
            json=query_payload
        )
        
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results:
                page_id = results[0].get("id")
                print(f"🔍 기존 페이지 발견: {user_input}")
                return page_id
            else:
                print(f"🆕 새 페이지 생성 필요: {user_input}")
                return None
        else:
            print(f"⚠️ 페이지 검색 실패: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"⚠️ 페이지 검색 중 오류: {e}")
        return None

def upload_to_notion(metadata: Dict[str, Any], user_input: str) -> Dict[str, Any]:
    """노션 데이터베이스에 페이지 생성 또는 업데이트 (하이브리드 방식)"""
    notion_token = os.getenv('NOTION_TOKEN')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    if not notion_token or not database_id:
        raise ValueError("NOTION_TOKEN 또는 NOTION_DATABASE_ID가 설정되지 않았습니다.")
    
    # 노션 API 헤더
    headers = {
        'Authorization': f'Bearer {notion_token}',
        'Content-Type': 'application/json',
        'Notion-Version': '2022-06-28'
    }
    
    # 1. 기존 페이지 검색
    existing_page_id = search_existing_page(user_input, headers, database_id)
    
    # 페이지 속성 생성 (신규/업데이트 구분)
    is_new_page = existing_page_id is None
    properties = create_notion_page_properties(metadata, user_input, is_new_page)
    
    if existing_page_id:
        # 2-A. 기존 페이지 업데이트
        payload = {"properties": properties}
        api_url = f"https://api.notion.com/v1/pages/{existing_page_id}"
        action = "업데이트"
        method = "PATCH"
    else:
        # 2-B. 새 페이지 생성
        payload = {
            "parent": {"database_id": database_id},
            "properties": properties
        }
        api_url = "https://api.notion.com/v1/pages"
        action = "생성"
        method = "POST"
    
    print(f"🚀 노션 페이지 {action} 중...")
    if metadata and "name" in metadata:
        print(f"📝 제목: {metadata['name']}")
    else:
        print(f"📝 제목: {user_input} (라프텔 정보 없음)")
    
    try:
        if method == "POST":
            response = requests.post(api_url, headers=headers, json=payload)
        else:
            response = requests.patch(api_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            page_data = response.json()
            page_id = page_data['id']
            page_url = page_data['url']
            
            print(f"✅ 노션 페이지 {action} 성공!")
            print(f"📄 페이지 ID: {page_id}")
            print(f"🔗 페이지 URL: {page_url}")
            
            return {
                "upload_success": True,
                "notion_page_id": page_id,
                "notion_page_url": page_url,
                "uploaded_fields": properties,
                "action": action
            }
        else:
            print(f"❌ 노션 페이지 {action} 실패:")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            return {
                "upload_success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "action": action
            }
            
    except Exception as e:
        print(f"❌ 노션 API 호출 실패: {e}")
        return {
            "upload_success": False,
            "error": str(e),
            "action": action
        }

def save_notion_results(result_data: Dict[str, Any], user_input: str):
    """노션 업로드 결과를 파일로 저장"""
    timestamp = datetime.now().strftime("%H%M%S")
    filename = f"results/notion_result_{timestamp}.json"
    
    # 타임스탬프와 사용자 입력 추가
    result_data["upload_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result_data["user_input"] = user_input
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 노션 결과 저장: {filename}")

def process_notion_upload(user_input: str = None):
    """4단계 메인 함수: 노션 페이지 생성"""
    print("="*50)
    print("🎯 4단계: 노션 페이지 생성")
    print("="*50)
    
    # 1. 메타데이터 결과 로드
    metadata_result = load_metadata_results()
    if not metadata_result:
        return
    
    # 2. 메타데이터 수집 성공 여부 확인
    if not metadata_result.get("metadata_success", False):
        print("❌ 3단계에서 메타데이터 수집에 실패했습니다. 노션 업로드를 건너뜁니다.")
        
        # 실패 결과 저장
        fail_result = {
            "upload_success": False,
            "error": "메타데이터 수집 실패로 인한 업로드 건너뜀"
        }
        save_notion_results(fail_result, metadata_result.get("user_input", "Unknown"))
        return
    
    # 3. 사용자 입력 정보 가져오기
    original_input = user_input or metadata_result.get("user_input", "Unknown")
    metadata = metadata_result.get("metadata", {})
    
    print(f"📝 원본 입력: {original_input}")
    print(f"🎬 선정된 애니메이션: {metadata.get('name', 'Unknown')}")
    
    # 4. 노션 페이지 생성
    upload_result = upload_to_notion(metadata, original_input)
    
    # 5. 결과 저장
    save_notion_results(upload_result, original_input)
    
    return upload_result

if __name__ == "__main__":
    # 테스트용 - 메타데이터 파일의 실제 user_input으로 테스트
    print("🧪 4단계 단독 테스트 시작")
    result = process_notion_upload()
    
    if result and result.get("upload_success"):
        print(f"\n🎉 4단계 테스트 성공!")
    else:
        print(f"\n💥 4단계 테스트 실패!")
