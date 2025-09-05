# 🎯 OpenAI Assistant 래퍼 클래스
"""
OpenAI Assistant API 래퍼 클래스
- 애니메이션 매칭을 위한 Assistant 호출
- 에러 핸들링 및 재시도 로직 포함
- 기존 step2 로직을 클래스로 래핑
"""

import openai
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import LLMMatchResult, SearchCandidate
from .config import settings

class OpenAIClient:
    """OpenAI Assistant 클라이언트"""
    
    def __init__(self):
        """클라이언트 초기화"""
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.assistant_id = settings.openai_assistant_id
        self.model = settings.openai_model
        self.temperature = settings.openai_temperature
        self.max_tokens = settings.openai_max_tokens
        self.retry_count = 3
        self.retry_delay = 2.0  # 초
    
    def _validate_setup(self) -> bool:
        """설정 유효성 검사"""
        if not settings.openai_api_key:
            print("❌ OpenAI API 키가 설정되지 않았습니다.")
            return False
            
        if not settings.openai_assistant_id:
            print("❌ OpenAI Assistant ID가 설정되지 않았습니다.")
            return False
            
        return True
    
    def _format_candidates_for_prompt(self, candidates: List[SearchCandidate]) -> str:
        """후보 목록을 프롬프트용 텍스트로 포맷"""
        if not candidates:
            return "후보 목록이 없습니다."
        
        formatted = []
        for i, candidate in enumerate(candidates, 1):
            formatted.append(f"{i}. {candidate.title}")
        
        return "\n".join(formatted)
    
    def find_best_match(self, user_input: str, candidates: List[SearchCandidate]) -> LLMMatchResult:
        """
        사용자 입력과 후보 목록을 기반으로 최적 매칭 찾기
        
        Args:
            user_input: 사용자가 입력한 애니메이션 제목
            candidates: 라프텔 검색 결과 후보 목록
            
        Returns:
            LLMMatchResult: LLM 매칭 결과
        """
        if not self._validate_setup():
            return LLMMatchResult(
                user_input=user_input,
                candidates_count=len(candidates),
                success=False,
                error_message="OpenAI 설정이 올바르지 않습니다."
            )
        
        try:
            print(f"🎯 2단계: '{user_input}' LLM 매칭 시작")
            print(f"📊 후보 제목 수: {len(candidates)}")
            print("✅ OpenAI 클라이언트 설정 완료")
            
            if not candidates:
                return LLMMatchResult(
                    user_input=user_input,
                    candidates_count=0,
                    success=False,
                    error_message="매칭할 후보가 없습니다."
                )
            
            # 후보 목록 포맷
            candidates_text = self._format_candidates_for_prompt(candidates)
            
            # Assistant 호출 메시지 구성
            user_message = f"""사용자 입력: "{user_input}"

후보 목록:
{candidates_text}

위 후보 목록에서 사용자 입력과 가장 유사한 애니메이션을 선택해주세요."""
            
            print(f"🤖 Assistant 호출 중... (ID: {self.assistant_id})")
            print("⏳ Assistant 처리 중...")
            
            # 재시도 로직 포함 Assistant 호출
            response_text = None
            for attempt in range(self.retry_count):
                try:
                    # 스레드 생성
                    thread = self.client.beta.threads.create()
                    
                    # 메시지 추가
                    self.client.beta.threads.messages.create(
                        thread_id=thread.id,
                        role="user",
                        content=user_message
                    )
                    
                    # Assistant 실행
                    run = self.client.beta.threads.runs.create(
                        thread_id=thread.id,
                        assistant_id=self.assistant_id
                    )
                    
                    # 실행 완료 대기
                    max_wait_time = 60  # 최대 60초 대기
                    wait_time = 0
                    while run.status in ['queued', 'in_progress', 'cancelling']:
                        time.sleep(2)
                        wait_time += 2
                        run = self.client.beta.threads.runs.retrieve(
                            thread_id=thread.id,
                            run_id=run.id
                        )
                        
                        if wait_time >= max_wait_time:
                            raise TimeoutError("Assistant 응답 시간 초과")
                    
                    if run.status == 'completed':
                        # 응답 메시지 가져오기
                        messages = self.client.beta.threads.messages.list(
                            thread_id=thread.id
                        )
                        
                        # Assistant의 마지막 응답 추출
                        for message in messages.data:
                            if message.role == "assistant":
                                response_text = message.content[0].text.value
                                break
                        
                        print("✅ Assistant 응답 수신 완료")
                        break
                    else:
                        error_msg = f"Assistant 실행 실패: {run.status}"
                        if hasattr(run, 'last_error') and run.last_error:
                            error_msg += f" - {run.last_error}"
                        raise Exception(error_msg)
                    
                except Exception as e:
                    print(f"⚠️ Assistant 호출 시도 {attempt + 1} 실패: {e}")
                    if attempt < self.retry_count - 1:
                        time.sleep(self.retry_delay)
                        continue
                    raise
            
            if not response_text:
                return LLMMatchResult(
                    user_input=user_input,
                    candidates_count=len(candidates),
                    success=False,
                    error_message="Assistant 응답을 받지 못했습니다."
                )
            
            # 응답 파싱
            result = self._parse_assistant_response(
                response_text, user_input, candidates
            )
            
            if result.success and result.selected_title:
                print(f"✅ 매칭 성공: {result.selected_title} (신뢰도: {result.confidence_score}%)")
            else:
                print(f"❌ 매칭 실패: {result.error_message}")
            
            return result
            
        except Exception as e:
            error_msg = f"OpenAI Assistant 호출 실패: {str(e)}"
            print(f"❌ {error_msg}")
            
            return LLMMatchResult(
                user_input=user_input,
                candidates_count=len(candidates),
                success=False,
                error_message=error_msg
            )
    
    def _parse_assistant_response(self, response_text: str, user_input: str, 
                                candidates: List[SearchCandidate]) -> LLMMatchResult:
        """Assistant 응답 파싱"""
        try:
            # JSON 형태의 응답인지 확인
            if '{' in response_text and '}' in response_text:
                try:
                    # JSON에서 추출 시도
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    json_str = response_text[json_start:json_end]
                    
                    response_data = json.loads(json_str)
                    
                    selected_title = response_data.get('selected_title')
                    confidence = response_data.get('confidence_score', 95)
                    reasoning = response_data.get('reasoning', '')
                    
                    if selected_title and selected_title.strip():
                        return LLMMatchResult(
                            user_input=user_input,
                            candidates_count=len(candidates),
                            selected_title=selected_title.strip(),
                            confidence_score=float(confidence),
                            reasoning=reasoning,
                            success=True
                        )
                        
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"⚠️ JSON 파싱 실패: {e}")
            
            # 텍스트 기반 파싱 시도
            # "선택: " 패턴 찾기
            if "선택:" in response_text:
                selected_part = response_text.split("선택:", 1)[1].split("\n")[0].strip()
                
                # 후보 목록에서 가장 유사한 제목 찾기
                for candidate in candidates:
                    if candidate.title in selected_part or selected_part in candidate.title:
                        return LLMMatchResult(
                            user_input=user_input,
                            candidates_count=len(candidates),
                            selected_title=candidate.title,
                            confidence_score=90.0,
                            reasoning=response_text,
                            success=True
                        )
            
            # 후보 번호 기반 파싱 시도 (예: "1.", "2." 등)
            for i, candidate in enumerate(candidates, 1):
                if f"{i}." in response_text or f"번째" in response_text:
                    return LLMMatchResult(
                        user_input=user_input,
                        candidates_count=len(candidates),
                        selected_title=candidate.title,
                        confidence_score=85.0,
                        reasoning=response_text,
                        success=True
                    )
            
            # 파싱 실패
            return LLMMatchResult(
                user_input=user_input,
                candidates_count=len(candidates),
                success=False,
                error_message=f"Assistant 응답을 파싱할 수 없습니다: {response_text[:100]}..."
            )
            
        except Exception as e:
            return LLMMatchResult(
                user_input=user_input,
                candidates_count=len(candidates),
                success=False,
                error_message=f"응답 파싱 중 오류: {str(e)}"
            )
