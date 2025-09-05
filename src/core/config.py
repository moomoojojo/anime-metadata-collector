# 🎯 통합 애니메이션 메타데이터 시스템 설정 파일
"""
통합된 설정 관리 클래스
- 기존 배치 처리 설정 유지
- 새로운 API 서버 설정 추가
- 환경별 설정 분리 (개발/프로덕션)
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
try:
    from pydantic_settings import BaseSettings
except ImportError:
    # pydantic v1 호환성 (pydantic_settings가 없는 경우)
    from pydantic import BaseSettings
from pydantic import Field

# 환경변수 로드
load_dotenv()

class AppSettings(BaseSettings):
    """애플리케이션 전체 설정"""
    
    # === 환경 감지 ===
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="API_DEBUG")
    
    # === API 키 설정 ===
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_assistant_id: str = Field(..., env="OPENAI_ASSISTANT_ID") 
    notion_token: str = Field(..., env="NOTION_TOKEN")
    notion_database_id: str = Field(..., env="NOTION_DATABASE_ID")
    laftel_api_key: Optional[str] = Field(default=None, env="LAFTEL_API_KEY")
    
    # === API 서버 설정 ===
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    allowed_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        env="ALLOWED_ORIGINS"
    )
    
    # === 로깅 설정 ===
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # === OpenAI 설정 ===
    openai_model: str = Field(default="gpt-4o-mini")
    openai_temperature: float = Field(default=0.1)
    openai_max_tokens: int = Field(default=1000)
    
    # === 라프텔 설정 ===
    max_search_candidates: int = Field(default=20)
    
    # === 배치 처리 설정 ===
    results_dir: str = Field(default="results")
    productions_dir: str = Field(default="productions")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def is_production(self) -> bool:
        """프로덕션 환경 여부"""
        return os.getenv("RENDER") == "true" or self.environment == "production"
    
    @property
    def cors_origins(self) -> list[str]:
        """CORS 허용 origin 리스트"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    def get_results_path(self, filename: str) -> str:
        """결과 파일 경로 생성"""
        os.makedirs(self.results_dir, exist_ok=True)
        return os.path.join(self.results_dir, filename)

# 전역 설정 인스턴스
settings = AppSettings()

# === 하위 호환성을 위한 레거시 변수들 ===
# 기존 코드에서 사용하던 변수명들을 유지
OPENAI_API_KEY = settings.openai_api_key
NOTION_TOKEN = settings.notion_token
NOTION_DATABASE_ID = settings.notion_database_id

OPENAI_MODEL = settings.openai_model
OPENAI_TEMPERATURE = settings.openai_temperature
OPENAI_MAX_TOKENS = settings.openai_max_tokens

MAX_SEARCH_CANDIDATES = settings.max_search_candidates

RESULTS_DIR = settings.results_dir
SEARCH_RESULTS_FILE = settings.get_results_path("search_results.json")
LLM_CHOICE_FILE = settings.get_results_path("llm_choice.json")
METADATA_FILE = settings.get_results_path("metadata.json")
NOTION_RESULT_FILE = settings.get_results_path("notion_result.json")

# 노션 필드 매핑 (기존 유지)
NOTION_FIELD_MAPPING = {
    "이름": "user_input",                # 사용자 입력 제목 (Title 칼럼)
    "라프텔 제목": "name",               # 라프텔에서 매칭된 제목
    "방영 분기": "air_year_quarter", 
    "라프텔 평점": "avg_rating",
    "방영 상태": "status",
    "라프텔 URL": "laftel_url",
    "표지": "cover_url",
    "제작사": "production",               # Select 타입
    "총 화수": "total_episodes"
}

# 신규 페이지 생성 시 기본값 설정 (기존 유지)
NOTION_DEFAULT_VALUES = {
    "상태": {"type": "status", "value": "관심 있음"},
    "분류": {"type": "select", "value": "애니메이션"},
    "시도 횟수": {"type": "number", "value": 0},
    "완료 횟수": {"type": "number", "value": 0}
}

def get_config() -> AppSettings:
    """설정 객체 반환"""
    return settings

def is_production() -> bool:
    """프로덕션 환경 여부 확인"""
    return settings.is_production
