#!/usr/bin/env python3
"""
전체 파이프라인 테스트 (1-4단계)
CSV의 첫 번째 항목으로 완전한 파이프라인 테스트
"""

import csv
import subprocess
import sys

def run_step(step_number, script_name, description):
    """단계별 스크립트 실행"""
    print(f"\n{'='*60}")
    print(f"🚀 {step_number}단계: {description}")
    print(f"📝 실행 스크립트: {script_name}")
    print('='*60)
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, encoding='utf-8')
        
        print(result.stdout)
        if result.stderr:
            print("⚠️ 경고/오류:")
            print(result.stderr)
            
        if result.returncode == 0:
            print(f"✅ {step_number}단계 성공!")
            return True
        else:
            print(f"❌ {step_number}단계 실패! (exit code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ {step_number}단계 실행 오류: {e}")
        return False

def main():
    """전체 파이프라인 실행"""
    print("🎯 전체 파이프라인 테스트 시작")
    print("📋 CSV 첫 번째 항목으로 1-4단계 순차 실행")
    
    # CSV 첫 번째 항목 확인
    try:
        with open('anime.csv', 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # 헤더 스킵
            first_anime = next(reader)[0]
        print(f"🎬 테스트 대상: {first_anime}")
    except Exception as e:
        print(f"❌ CSV 파일 읽기 실패: {e}")
        return
    
    # 단계별 실행
    steps = [
        (1, "step1_search_candidates.py", "라프텔 검색 후보 수집"),
        (2, "step2_llm_matching.py", "OpenAI LLM 스마트 매칭"),
        (3, "step3_metadata_collection.py", "메타데이터 수집"),
        (4, "step4_notion_upload.py", "노션 페이지 생성")
    ]
    
    success_count = 0
    for step_num, script, desc in steps:
        if run_step(step_num, script, desc):
            success_count += 1
        else:
            print(f"\n💥 {step_num}단계에서 파이프라인 중단됨")
            break
    
    # 최종 결과
    print(f"\n{'='*60}")
    print(f"🏁 전체 파이프라인 테스트 완료")
    print(f"✅ 성공한 단계: {success_count}/4")
    
    if success_count == 4:
        print("🎉 전체 파이프라인 성공! 모든 단계가 완벽하게 작동합니다!")
    else:
        print(f"💥 파이프라인 실패: {4-success_count}개 단계에서 문제 발생")

if __name__ == "__main__":
    main()
