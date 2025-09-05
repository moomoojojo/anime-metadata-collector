#!/usr/bin/env python3
"""
빠른 개발 중 테스트 스크립트
각 Phase 완료시 바로 실행해서 기본 동작 확인용
"""
import sys
import os
import importlib.util
import subprocess
import json
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_phase_1():
    """Phase 1: 설정 파일들 기본 검증"""
    print("🔍 Phase 1 테스트: 설정 파일 검증")
    
    # render.yaml 문법 확인
    try:
        import yaml
        with open('render.yaml', 'r') as f:
            config = yaml.safe_load(f)
        print("✅ render.yaml 문법 정상")
        print(f"   - 서비스명: {config['services'][0]['name']}")
    except Exception as e:
        print(f"❌ render.yaml 문제: {e}")
        return False
    
    # requirements-api.txt 설치 가능 여부 확인 (가상환경 권장)
    print("📦 requirements-api.txt 의존성 체크 중...")
    try:
        # 실제로 설치하지는 않고 문법만 확인
        with open('requirements-api.txt', 'r') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            print(f"✅ 의존성 {len(lines)}개 확인됨")
    except Exception as e:
        print(f"❌ requirements-api.txt 문제: {e}")
        return False
    
    return True

def test_phase_2():
    """Phase 2: 코어 모듈들 기본 임포트 테스트"""
    print("\n🔍 Phase 2 테스트: 코어 모듈 임포트")
    
    modules_to_test = [
        'src.core.config',
        'src.core.models', 
        'src.core.pipeline',
        'src.core.laftel_client',
        'src.core.openai_client',
        'src.core.notion_client'
    ]
    
    success_count = 0
    for module_name in modules_to_test:
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                print(f"⏭️  {module_name}: 아직 미생성 (정상)")
            else:
                # 실제 임포트 시도
                module = importlib.import_module(module_name)
                print(f"✅ {module_name}: 임포트 성공")
                success_count += 1
        except Exception as e:
            print(f"❌ {module_name}: 임포트 실패 - {e}")
    
    print(f"📊 코어 모듈 상태: {success_count}/{len(modules_to_test)} 완료")
    return True

def test_phase_3():
    """Phase 3: API 서버 기본 동작 테스트"""
    print("\n🔍 Phase 3 테스트: API 서버 테스트")
    
    # FastAPI 앱 임포트 시도
    try:
        from src.api.main import app
        print("✅ FastAPI 앱 임포트 성공")
    except Exception as e:
        print(f"❌ FastAPI 앱 임포트 실패: {e}")
        return False
    
    # TODO: 실제 서버 시작 및 헬스체크 테스트
    # 여기서는 기본 구조만 확인
    print("🚀 로컬 서버 테스트는 수동으로 실행:")
    print("   python -m uvicorn src.api.main:app --reload")
    print("   curl http://localhost:8000/health")
    
    return True

def test_phase_4():
    """Phase 4: 기존 배치 기능 회귀 테스트"""
    print("\n🔍 Phase 4 테스트: 배치 기능 회귀 테스트")
    
    # 기존 모듈들 임포트 테스트
    legacy_modules = [
        'src.anime_metadata.config',
        'src.batch.processor'
    ]
    
    for module_name in legacy_modules:
        try:
            spec = importlib.util.find_spec(module_name)
            if spec:
                print(f"✅ {module_name}: 여전히 접근 가능")
            else:
                print(f"⚠️  {module_name}: 구조 변경됨 - 확인 필요")
        except Exception as e:
            print(f"❌ {module_name}: 문제 - {e}")
    
    return True

def main():
    """선택한 Phase 테스트 실행"""
    if len(sys.argv) != 2:
        print("사용법: python scripts/quick_test.py <phase_number>")
        print("예시: python scripts/quick_test.py 1")
        sys.exit(1)
    
    phase = sys.argv[1]
    
    print(f"🧪 Phase {phase} 빠른 검증 시작")
    print("=" * 50)
    
    if phase == '1':
        success = test_phase_1()
    elif phase == '2':
        success = test_phase_2()
    elif phase == '3':
        success = test_phase_3()
    elif phase == '4':
        success = test_phase_4()
    else:
        print("❌ 유효하지 않은 Phase 번호. 1-4만 지원됩니다.")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    if success:
        print(f"🎉 Phase {phase} 기본 검증 완료!")
    else:
        print(f"⚠️  Phase {phase}에서 문제 발견 - 수정 후 재테스트 권장")
        sys.exit(1)

if __name__ == "__main__":
    main()
