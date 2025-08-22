# 🎬 애니메이션 메타데이터 자동 입력

> 애니메이션 제목만 입력하면 노션에 완벽한 메타데이터가 자동으로! ✨

## 👥 누가 쓰면 좋나요?

**애니메이션에 대한 메타데이터를 자동으로 집어넣고 싶은 노션 기록 덕후**

- 🎯 애니메이션 시청 기록을 체계적으로 관리하고 싶은 분
- 📊 라프텔 메타데이터(제작사, 방영분기, 평점 등)를 자동으로 수집하고 싶은 분  
- ⏰ 수작업으로 데이터 입력하는 시간을 절약하고 싶은 분

## 🚀 어떻게 동작하나요?

```
📄 CSV에 제목 입력  →  🔍 라프텔 검색  →  🤖 AI 매칭  →  📊 메타데이터 수집  →  📝 노션 업로드
```

1. **애니메이션 제목**을 CSV 파일에 입력하고
2. **라프텔 비공식 API**를 조회하면 최대 20개의 애니메이션 제목 리스트 반환됨
3. **OpenAI Assistant**로 리스트 중에서 유사도 가장 높은 애니메이션 제목 하나 선택
4. 해당 애니메이션 제목으로 **애니메이션 메타데이터 가져옴**
5. **애니메이션 메타데이터를 노션 데이터베이스에 밀어넣어줌**

## 🤖 왜 AI를 사용하나요?

시즌이 여러개인 경우, 극장판/TVA/OVA가 다양하게 있는 경우 입력한 애니메이션 제목에 대한 후보군이 엄청 나와요. 

**입력된 애니메이션 제목과 가장 유사한 걸 선택할 수 있도록 LLM을 사용합니다!** 🎯

## ⚡ 빠른 시작

### 1️⃣ **설치**
```bash
git clone https://github.com/moomoojojo/jojo_study.git
cd "애니메이션 메타데이터 자동 입력"
pip install -r requirements.txt
```

### 2️⃣ **API 키 설정**
```bash
cp env.example .env
```

`.env` 파일에 다음 정보를 입력해주세요:
```
OPENAI_API_KEY=sk-proj-xxxxx
OPENAI_ASSISTANT_ID=asst_xxxxx  
NOTION_TOKEN=ntn_xxxxx
NOTION_DATABASE_ID=xxxxx-xxxxx
```

### 3️⃣ **애니메이션 제목 입력**
`anime.csv` 파일에 애니메이션 제목을 입력하세요:
```csv
애니메이션 제목
스파이 패밀리 1기
무직전생 1기  
타코피의 원죄
```

### 4️⃣ **실행!**
```bash
python3 src/anime_metadata/tools/batch_processor.py --csv anime.csv --description "내 첫 번째 배치"
```

### 5️⃣ **결과 확인**
```bash
python3 src/anime_metadata/tools/check_status.py
```

## 📊 어떤 데이터를 수집하나요?

| 🏷️ **데이터** | 📝 **설명** | 🌟 **예시** |
|---|---|---|
| 라프텔 제목 | 정확한 공식 제목 | "SPY×FAMILY part 1" |
| 방영분기 | 언제 방영했는지 | "2022년 2분기" |
| 평점 | 라프텔 사용자 평점 | "4.7" |
| 제작사 | 애니메이션 스튜디오 | "Wit Studio, CloverWorks" |
| 총 화수 | 전체 에피소드 수 | "12화" |
| 표지 | 고화질 포스터 이미지 | 🖼️ |
| 라프텔 URL | 해당 페이지 링크 | 🔗 |

## 💡 권장 사용 방식

1. **메타데이터만 필요하신 분**: 3단계까지만 실행하세요
2. **노션 기록 덕후**: 4단계까지 완주하시길! 😊

## 🔧 고급 사용법

<details>
<summary><strong>📋 노션 데이터베이스 설정</strong></summary>

다음 칼럼들을 노션 데이터베이스에 미리 만들어주세요:

| 칼럼명 | 타입 | 설명 |
|---|---|---|
| **이름** | Title | 사용자 입력 제목 |
| **라프텔 제목** | Rich Text | 매칭된 공식 제목 |
| **방영 분기** | Multi-select | 방영 시기 |
| **라프텔 평점** | Number | 평점 |
| **제작사** | Select | 제작 스튜디오 |
| **총 화수** | Number | 에피소드 수 |
| **표지** | URL | 포스터 이미지 |
| **라프텔 URL** | URL | 라프텔 링크 |

</details>

<details>
<summary><strong>🛠️ 개별 단계 실행</strong></summary>

```bash
# 1단계: 라프텔 검색
python3 src/anime_metadata/step1_search_candidates.py

# 2단계: AI 매칭  
python3 src/anime_metadata/step2_llm_matching.py

# 3단계: 메타데이터 수집
python3 src/anime_metadata/step3_metadata_collection.py

# 4단계: 노션 업로드
python3 src/anime_metadata/step4_notion_upload.py
```

</details>

<details>
<summary><strong>🤖 OpenAI Assistant 설정</strong></summary>

1. [OpenAI Platform](https://platform.openai.com/) → Assistant 생성
2. Model: `gpt-4o` 또는 `gpt-4o-mini` 선택
3. [시스템 프롬프트는 여기서 확인](docs/system_prompt.md)
4. Assistant ID를 `.env`에 추가

</details>

## 🆘 문제가 생겼나요?

### **💬 자주 묻는 질문**
- **Q**: 매칭이 잘못되었어요!
- **A**: 제목을 더 정확하게 입력해보세요. 예: "리제로 3기" → "Re: 제로부터 시작하는 이세계 생활 3기"

- **Q**: 노션 업로드가 안 돼요!
- **A**: 노션 Integration 권한과 데이터베이스 ID를 확인해주세요.

- **Q**: 일부만 실행되고 멈췄어요!
- **A**: `python3 src/anime_metadata/tools/resume_failed.py`로 이어서 실행하세요.

### **📞 더 많은 도움이 필요하다면**
- 🐛 [이슈 등록](https://github.com/moomoojojo/jojo_study/issues)
- 📖 [자세한 설명서](docs/)
- 🧪 [사용 예제](examples/)

---

❤️ **노션 덕후들을 위한 자동화 도구**  
🤖 **Python + OpenAI + Laftel + Notion**

⭐ 도움이 되셨다면 Star를 눌러주세요!