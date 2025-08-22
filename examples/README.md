# 📄 사용 예시

이 폴더에는 애니메이션 메타데이터 자동 입력 시스템을 테스트할 수 있는 예시 파일들이 있습니다.

## 📋 sample_anime.csv

**즉시 테스트 가능한 애니메이션 목록:**
- 무직전생 ~이세계에 갔으면 최선을 다한다~ 1기
- 스파이 패밀리 1기  
- 장송의 프리렌 1기
- Re: 제로부터 시작하는 이세계 생활 3기
- 최애의 아이

## 🚀 실행 방법

```bash
# 예시 파일로 배치 실행
python3 src/anime_metadata/tools/batch_processor.py --csv examples/sample_anime.csv --description "첫 번째 테스트"

# 진행 상황 확인
python3 src/anime_metadata/tools/check_status.py
```

## ✅ 예상 결과

- **성공 예상**: 무직전생, 스파이 패밀리, 장송의 프리렌, Re: 제로 3기
- **매칭 어려움 가능**: 최애의 아이 (여러 시즌 존재)

## 🎯 직접 테스트해보기

1. 이 파일을 복사해서 `my_anime.csv` 생성
2. 원하는 애니메이션 제목 추가/수정
3. 배치 실행
4. 노션 데이터베이스에서 결과 확인

**즐거운 애니메이션 기록 관리 되세요!** 🎬✨
