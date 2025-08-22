#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2단계: OpenAI Assistant를 활용한 스마트 애니메이션 매칭

1단계에서 수집된 후보 제목들을 OpenAI Assistant에게 제공하여
사용자 입력과 가장 유사한 애니메이션을 선택하거나 매칭 불가 판단
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import openai
from dotenv import load_dotenv
import config

def load_search_results() -> Dict[str, Any]:
    """1단계에서 생성된 검색 결과 로드 (최신 파일 자동 감지)"""
    try:
        import glob
        
        # results 디렉토리에서 search_results_*.json 파일들 찾기
        search_pattern = os.path.join(config.RESULTS_DIR, "search_results_*.json")
        search_files = glob.glob(search_pattern)
        
        if not search_files:
            print(f"❌ 검색 결과 파일을 찾을 수 없습니다: {search_pattern}")
            print("💡 먼저 step1_search_candidates.py를 실행해주세요.")
            return {}
        
        # 가장 최신 파일 선택 (파일명에 타임스탬프가 포함되어 있음)
        latest_file = max(search_files, key=os.path.getctime)
        print(f"📥 최신 검색 결과 로드: {latest_file}")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    except Exception as e:
        print(f"❌ 검색 결과 로드 실패: {e}")
        return {}

def setup_openai_client() -> Optional[openai.OpenAI]:
    """OpenAI 클라이언트 설정"""
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "여기에_실제_API_키_입력해주세요":
        print("❌ OpenAI API 키가 설정되지 않았습니다.")
        print("💡 .env 파일에서 OPENAI_API_KEY를 확인해주세요.")
        return None
    
    try:
        client = openai.OpenAI(api_key=api_key)
        print("✅ OpenAI 클라이언트 설정 완료")
        return client
    except Exception as e:
        print(f"❌ OpenAI 클라이언트 설정 실패: {e}")
        return None

def call_assistant_matching(client: openai.OpenAI, user_input: str, candidate_titles: list) -> Dict[str, Any]:
    """OpenAI Assistant 호출하여 매칭 수행"""
    assistant_id = os.getenv("OPENAI_ASSISTANT_ID")
    
    if not assistant_id:
        raise ValueError("OPENAI_ASSISTANT_ID가 설정되지 않았습니다.")
    
    print(f"🤖 Assistant 호출 중... (ID: {assistant_id})")
    
    try:
        # Thread 생성
        thread = client.beta.threads.create()
        
        # 매칭 요청 메시지 구성
        matching_request = {
            "user_input": user_input,
            "candidates": candidate_titles
        }
        
        message_content = f"""
다음 애니메이션 제목 매칭을 요청합니다:

**사용자 입력:** {user_input}

**후보 제목들:**
{chr(10).join([f"{i+1}. {title}" for i, title in enumerate(candidate_titles)])}

위의 후보들 중에서 사용자 입력과 가장 적합한 애니메이션을 선택하거나, 
적합한 매칭이 없다면 매칭 불가로 판단해주세요.

반드시 JSON 형태로 응답해주세요.
"""
        
        # 메시지 전송
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message_content
        )
        
        # Assistant 실행
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )
        
        # 실행 완료 대기
        print("⏳ Assistant 처리 중...")
        while run.status in ['queued', 'in_progress']:
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
        
        if run.status == 'completed':
            # 응답 메시지 가져오기
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            assistant_response = messages.data[0].content[0].text.value
            
            print("✅ Assistant 응답 수신 완료")
            return {
                "success": True,
                "assistant_response": assistant_response,
                "thread_id": thread.id,
                "run_id": run.id
            }
        else:
            print(f"❌ Assistant 실행 실패: {run.status}")
            if hasattr(run, 'last_error'):
                print(f"오류 상세: {run.last_error}")
            
            return {
                "success": False,
                "error": f"Assistant 실행 실패: {run.status}",
                "thread_id": thread.id,
                "run_id": run.id
            }
            
    except Exception as e:
        print(f"❌ Assistant 호출 중 오류: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def parse_assistant_response(response_text: str) -> Dict[str, Any]:
    """Assistant 응답을 파싱하여 구조화된 데이터 반환"""
    try:
        # JSON 부분 추출 시도
        import re
        
        # ```json...``` 형태로 감싸진 경우
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 직접 JSON이 포함된 경우
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("응답에서 JSON을 찾을 수 없습니다.")
        
        # JSON 파싱
        parsed_result = json.loads(json_str)
        
        # 필수 필드 검증
        required_fields = ["status", "selected_title", "confidence", "reason"]
        for field in required_fields:
            if field not in parsed_result:
                raise ValueError(f"필수 필드 누락: {field}")
        
        return {
            "parse_success": True,
            "parsed_result": parsed_result
        }
        
    except Exception as e:
        print(f"❌ Assistant 응답 파싱 실패: {e}")
        print(f"원본 응답: {response_text}")
        
        return {
            "parse_success": False,
            "error": str(e),
            "raw_response": response_text
        }

def perform_llm_matching(user_input: str, candidate_titles: list) -> Dict[str, Any]:
    """LLM 매칭 수행"""
    print(f"\n🎯 2단계: '{user_input}' LLM 매칭 시작")
    print(f"📊 후보 제목 수: {len(candidate_titles)}")
    
    # OpenAI 클라이언트 설정
    client = setup_openai_client()
    if not client:
        return {
            "user_input": user_input,
            "candidate_titles": candidate_titles,
            "llm_timestamp": datetime.now().isoformat(),
            "matching_success": False,
            "error_message": "OpenAI 클라이언트 설정 실패"
        }
    
    # Assistant 호출
    assistant_result = call_assistant_matching(client, user_input, candidate_titles)
    
    if not assistant_result["success"]:
        return {
            "user_input": user_input,
            "candidate_titles": candidate_titles,
            "llm_timestamp": datetime.now().isoformat(),
            "matching_success": False,
            "error_message": assistant_result["error"],
            "assistant_raw": assistant_result
        }
    
    # Assistant 응답 파싱
    parse_result = parse_assistant_response(assistant_result["assistant_response"])
    
    result_data = {
        "user_input": user_input,
        "candidate_titles": candidate_titles,
        "llm_timestamp": datetime.now().isoformat(),
        "matching_success": parse_result["parse_success"],
        "assistant_raw_response": assistant_result["assistant_response"],
        "thread_id": assistant_result["thread_id"],
        "run_id": assistant_result["run_id"]
    }
    
    if parse_result["parse_success"]:
        parsed = parse_result["parsed_result"]
        result_data.update({
            "match_status": parsed["status"],
            "selected_title": parsed["selected_title"],
            "confidence": parsed["confidence"],
            "reason": parsed["reason"]
        })
        
        if parsed["status"] == "match_found":
            print(f"✅ 매칭 성공: {parsed['selected_title']} (신뢰도: {parsed['confidence']}%)")
        else:
            print(f"❌ 매칭 불가: {parsed['reason']}")
    else:
        result_data.update({
            "parse_error": parse_result["error"],
            "raw_response": parse_result["raw_response"]
        })
        print("❌ Assistant 응답 파싱 실패")
    
    return result_data

def save_llm_results(results: Dict[str, Any]) -> None:
    """LLM 매칭 결과를 JSON 파일로 저장"""
    try:
        os.makedirs(config.RESULTS_DIR, exist_ok=True)
        with open(config.LLM_CHOICE_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"💾 LLM 결과 저장: {config.LLM_CHOICE_FILE}")
    except Exception as e:
        print(f"❌ 저장 실패: {e}")

def main():
    """메인 실행 함수"""
    print("🚀 2단계: OpenAI LLM 매칭 시작")
    print("="*80)
    
    # 1단계 결과 로드
    search_results = load_search_results()
    if not search_results:
        print("❌ 1단계 결과를 찾을 수 없습니다. 먼저 step1을 실행해주세요.")
        return
    
    if not search_results.get("search_success", False):
        print("❌ 1단계 검색이 실패했습니다.")
        return
    
    user_input = search_results["user_input"]
    candidate_titles = search_results["candidate_titles"]
    
    if not candidate_titles:
        print("❌ 후보 제목이 없습니다.")
        return
    
    print(f"📥 1단계 결과 로드 완료:")
    print(f"   - 사용자 입력: {user_input}")
    print(f"   - 후보 수: {len(candidate_titles)}")
    
    # LLM 매칭 수행
    llm_results = perform_llm_matching(user_input, candidate_titles)
    
    # 결과 저장
    save_llm_results(llm_results)
    
    print("\n" + "="*80)
    print("✅ 2단계 완료!")
    
    if llm_results.get("matching_success"):
        if llm_results.get("match_status") == "match_found":
            print(f"🎯 매칭 결과: {llm_results['selected_title']}")
            print(f"🔍 신뢰도: {llm_results['confidence']}%")
            print(f"📝 이유: {llm_results['reason']}")
        else:
            print("❌ 매칭 불가")
            print(f"📝 이유: {llm_results['reason']}")
    else:
        print("❌ LLM 매칭 실패")

if __name__ == "__main__":
    main()
