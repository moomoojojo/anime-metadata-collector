# 🎯 스마트 매칭 시스템 설정 파일
# Git 변화 테스트: 2024년 업데이트
import os
from dotenv import load_dotenv

load_dotenv()

# API 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# OpenAI 설정
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_TEMPERATURE = 0.1
OPENAI_MAX_TOKENS = 1000

# 라프텔 설정
MAX_SEARCH_CANDIDATES = 20  # 상위 몇 개 후보까지 수집할지

# 결과 저장 경로
RESULTS_DIR = "results"
SEARCH_RESULTS_FILE = f"{RESULTS_DIR}/search_results.json"
LLM_CHOICE_FILE = f"{RESULTS_DIR}/llm_choice.json"
METADATA_FILE = f"{RESULTS_DIR}/metadata.json"
NOTION_RESULT_FILE = f"{RESULTS_DIR}/notion_result.json"

# 노션 필드 매핑 (업데이트 버전)
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
