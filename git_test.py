#!/usr/bin/env python3
"""
Git 변화 테스트를 위한 임시 파일

이 파일은 Cursor의 Git Changes 뷰 테스트를 위해 생성되었습니다.
"""

import datetime

def get_current_time():
    """현재 시간을 반환하는 함수"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def test_git_changes():
    """Git 변화 테스트 함수"""
    print("🧪 Git Changes 테스트 중...")
    print(f"📅 생성 시간: {get_current_time()}")
    print("✅ 새 파일이 성공적으로 생성되었습니다!")

if __name__ == "__main__":
    test_git_changes()
