# 🔄 하위 호환성 레이어
"""
기존 코드와의 호환성 유지를 위한 래퍼
- 기존 import 경로 유지
- 새로운 코어 모듈로 리다이렉트
- 점진적 마이그레이션 지원
"""

import warnings
import sys
from pathlib import Path

# 새로운 코어 모듈들을 기존 경로로 노출
try:
    # 프로젝트 루트를 경로에 추가
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # 새 코어 모듈들 import
    from src.core.config import settings as new_settings
    from src.core.pipeline import AnimePipeline
    from src.batch.processor import BatchProcessor as NewBatchProcessor
    
    # 하위 호환성 경고
    def _deprecation_warning(old_path: str, new_path: str):
        warnings.warn(
            f"'{old_path}'는 deprecated입니다. '{new_path}'를 사용하세요.",
            DeprecationWarning,
            stacklevel=3
        )
    
    # 기존 설정들을 새 설정으로 리다이렉트
    class LegacyConfig:
        """기존 config 모듈 호환성"""
        
        def __getattr__(self, name):
            # 자주 사용되는 설정들 매핑
            mapping = {
                'OPENAI_API_KEY': new_settings.openai_api_key,
                'NOTION_TOKEN': new_settings.notion_token,
                'NOTION_DATABASE_ID': new_settings.notion_database_id,
                'OPENAI_MODEL': new_settings.openai_model,
                'OPENAI_TEMPERATURE': new_settings.openai_temperature,
                'MAX_SEARCH_CANDIDATES': new_settings.max_search_candidates,
                'RESULTS_DIR': new_settings.results_dir,
                'NOTION_FIELD_MAPPING': getattr(new_settings, 'notion_field_mapping', {}),
                'NOTION_DEFAULT_VALUES': getattr(new_settings, 'notion_default_values', {})
            }
            
            if name in mapping:
                return mapping[name]
            
            # 새 설정에서 찾기 시도
            if hasattr(new_settings, name.lower()):
                return getattr(new_settings, name.lower())
            
            raise AttributeError(f"'{name}' 설정을 찾을 수 없습니다.")
    
    # 기존 BatchProcessor 래퍼
    class LegacyBatchProcessor(NewBatchProcessor):
        """기존 BatchProcessor 인터페이스 호환성"""
        
        def __init__(self, *args, **kwargs):
            _deprecation_warning(
                "src.anime_metadata.tools.batch_processor.BatchProcessor",
                "src.batch.processor.BatchProcessor"
            )
            super().__init__(*args, **kwargs)
    
    # 호환성 객체들 생성
    config = LegacyConfig()
    BatchProcessor = LegacyBatchProcessor
    
    # 파이프라인도 노출 (새로운 기능)
    pipeline = AnimePipeline()
    
except ImportError as e:
    # 새 모듈을 불러올 수 없는 경우 원래 모듈 사용
    print(f"⚠️ 새 코어 모듈 로드 실패, 기존 모듈 사용: {e}")
    
    # 기존 config 모듈 그대로 사용  
    from . import config
    from .tools.batch_processor import BatchProcessor
    
    # 파이프라인은 사용할 수 없음
    pipeline = None

# 모듈 정보
__version__ = "2.0.0-legacy-compat"
__legacy_support__ = True

def get_migration_info():
    """마이그레이션 정보 반환"""
    return {
        "legacy_modules": [
            "src.anime_metadata.config",
            "src.anime_metadata.tools.batch_processor.BatchProcessor"
        ],
        "new_modules": [
            "src.core.config.settings",  
            "src.batch.processor.BatchProcessor",
            "src.core.pipeline.AnimePipeline"
        ],
        "migration_status": "완료" if 'NewBatchProcessor' in locals() else "부분완료",
        "recommended_action": "새 모듈 사용 권장"
    }

def test_compatibility():
    """호환성 테스트"""
    try:
        # 기존 방식으로 접근 테스트
        _ = config.OPENAI_API_KEY
        _ = BatchProcessor
        
        print("✅ 기존 모듈 접근 호환성 유지됨")
        return True
        
    except Exception as e:
        print(f"❌ 호환성 문제: {e}")
        return False

if __name__ == "__main__":
    print("🔄 하위 호환성 테스트")
    print(f"버전: {__version__}")
    print()
    
    # 호환성 테스트 실행
    test_compatibility()
    
    # 마이그레이션 정보 출력
    info = get_migration_info()
    print(f"\n📊 마이그레이션 정보:")
    print(f"   상태: {info['migration_status']}")
    print(f"   권장사항: {info['recommended_action']}")
