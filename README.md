# 🎬 콘티·대본·음악까지 한 번에: AI 숏폼 콘텐츠 어시스턴트

## 📌 개요
유튜브 영상 2개를 입력하면, 자막·메타데이터를 자동 수집해  
**영상별 상세 분석 → 종합 주제 추천 → 맞춤 대본 생성 → 3초 단위 콘티 → 음악 추천**  
까지 한 번에 만들어주는 **Streamlit 기반 웹 앱**입니다.

---


## 👥 참여인원
- **총 4명 (비개발자)**  


---


## 🖥 시스템 환경

### 런타임 / 언어
- Python 3.10+

### 주요 라이브러리
- **Streamlit**: 웹 UI 프레임워크
- **openai**: GPT-4o 호출
- **youtube-transcript-api**: 자막(Transcript) 수집
- **requests**: YouTube Data API v3 호출
- `urllib.parse`: 유튜브 URL 파싱

### 외부 API / 인증
- **OpenAI API** (GPT-4o)
- **YouTube Data API v3**
- 비밀키 관리는 **`st.secrets`** 사용
    - `OPENAI_API_KEY`
    - `YOUTUBE_API_KEY`
