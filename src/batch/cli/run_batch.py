#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
새로운 배치 처리 CLI 실행기
- 리팩토링된 BatchProcessor 사용
- 기존 인터페이스 호환성 유지
- 코어 모듈 기반으로 동작
"""

import os
import sys
import argparse
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.batch.processor import BatchProcessor

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description='애니메이션 메타데이터 배치 처리 (리팩토링 버전)',
        epilog='예시: python run_batch.py --csv anime.csv --description "첫 번째 테스트"'
    )
    
    parser.add_argument(
        '--csv', 
        required=True, 
        help='처리할 애니메이션 목록 CSV 파일'
    )
    parser.add_argument(
        '--description', 
        default='', 
        help='배치 처리 설명'
    )
    parser.add_argument(
        '--db-id', 
        help='노션 데이터베이스 ID (기본값 사용하려면 생략)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='실제 실행 없이 설정만 확인'
    )
    
    args = parser.parse_args()
    
    # CSV 파일 존재 확인
    if not os.path.exists(args.csv):
        print(f"❌ CSV 파일을 찾을 수 없습니다: {args.csv}")
        return 1
    
    # dry-run 모드
    if args.dry_run:
        print("🧪 Dry-run 모드: 설정 확인만 수행")
        try:
            processor = BatchProcessor(args.csv, args.description, args.db_id)
            anime_list = processor.load_anime_list()
            
            print(f"✅ 설정 확인 완료")
            print(f"📁 CSV 파일: {args.csv}")
            print(f"📄 설명: {args.description}")
            print(f"🎯 처리 대상: {len(anime_list)}개 애니메이션")
            print(f"📂 결과 폴더: {processor.batch_folder}")
            
            if args.db_id:
                print(f"🗄️ 노션 DB ID: {args.db_id}")
            else:
                print(f"🗄️ 노션 DB ID: 기본값 사용")
            
            print("\n📋 처리 예정 애니메이션:")
            for i, title in enumerate(anime_list[:5], 1):
                print(f"   {i}. {title}")
            
            if len(anime_list) > 5:
                print(f"   ... 외 {len(anime_list) - 5}개")
            
            print("\n💡 실제 실행하려면 --dry-run 옵션을 제거하세요")
            return 0
            
        except Exception as e:
            print(f"❌ 설정 확인 실패: {e}")
            return 1
    
    # 실제 배치 실행
    print(f"🚀 배치 처리 시작")
    print(f"📁 CSV: {args.csv}")
    print(f"📄 설명: {args.description}")
    
    try:
        processor = BatchProcessor(args.csv, args.description, args.db_id)
        success = processor.run_batch()
        
        if success:
            print(f"\n🎉 배치 처리 완료!")
            print(f"📂 결과 확인: python src/batch/cli/check_status.py --batch-id {processor.batch_id}")
            return 0
        else:
            print(f"\n❌ 배치 처리 실패")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n❌ 사용자에 의해 중단됨")
        return 1
    except Exception as e:
        print(f"❌ 배치 처리 실패: {e}")
        import traceback
        if os.getenv("DEBUG"):
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
