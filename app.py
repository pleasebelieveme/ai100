import os
import re
import streamlit as st
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
import requests
from urllib.parse import urlparse, parse_qs
from requests.exceptions import ConnectionError

# API 키 설정
os.environ["OPENAI_API_KEY"] = st.secrets['OPENAI_API_KEY']
os.environ["YOUTUBE_API_KEY"] = st.secrets['YOUTUBE_API_KEY']
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 방문자 수 초기화 및 증가
if 'visitor_count' not in st.session_state:
    st.session_state['visitor_count'] = 0

st.session_state['visitor_count'] += 1

# 사이드바 제목 및 설명 추가
st.sidebar.title("mypage")

# 텍스트 입력
name = st.sidebar.text_input("name:")

# CREATIVE 글자를 가운데 정렬하고 폰트와 크기 설정
st.markdown("<div style='text-align: center; font-size: 100px; font-family: Georgia, serif'>CREATIVE</div>", unsafe_allow_html=True)

video_url1 = st.text_input("첫 번째 YouTube 영상 URL을 입력하세요")
video_url2 = st.text_input("두 번째 YouTube 영상 URL을 입력하세요")

def get_video_id(url):
    parsed_url = urlparse(url)
    if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        video_id = parse_qs(parsed_url.query).get('v')
        if video_id:
            return video_id[0]
    elif parsed_url.hostname in ['youtu.be']:
        return parsed_url.path[1:]
    return None

def get_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
        return transcript
    except NoTranscriptFound:
        return None
    except Exception as e:
        st.error(f"대본을 가져오는 데 실패했습니다: {e}")
        return None

def get_video_details(video_id):
    YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={YOUTUBE_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        video_info = response.json()
        if 'items' in video_info and len(video_info['items']) > 0:
            title = video_info['items'][0]['snippet']['title']
            description = video_info['items'][0]['snippet']['description']
            return title, description
    except ConnectionError as e:
        st.error(f"네트워크 연결 오류가 발생했습니다: {e}")
    except Exception as e:
        st.error(f"비디오 정보를 가져오는 데 실패했습니다: {e}")
    return None, None

def format_transcript(transcript):
    transcript_text = ""
    for item in transcript:
        start_time = item['start']
        duration = item['duration']
        text = item['text']
        transcript_text += f"[{start_time} - {start_time + duration}] {text}\n"
    return transcript_text

def truncate_text(text, max_length=4000):
    if len(text) > max_length:
        return text[:max_length]
    return text

if 'analysis_1' not in st.session_state:
    st.session_state.analysis_1 = ""
if 'analysis_2' not in st.session_state:
    st.session_state.analysis_2 = ""
if 'combined_recommendations' not in st.session_state:
    st.session_state.combined_recommendations = ""
if 'script_result' not in st.session_state:
    st.session_state.script_result = ""
if 'production_result' not in st.session_state:
    st.session_state.production_result = ""
if 'music_result' not in st.session_state:
    st.session_state.music_result = ""

def escape_js_string(s):
    return s.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"').replace("'", "\\'")

def save_to_local_storage(key, value):
    escaped_value = escape_js_string(value)
    st.markdown(f"""
    <script>
    localStorage.setItem("{key}", `{escaped_value}`);
    </script>
    """, unsafe_allow_html=True)

def load_from_local_storage(key):
    load_script = f"""
    <script>
    const value = localStorage.getItem("{key}");
    if (value) {{
        const element = document.getElementById('{key}');
        if (element) {{
            element.innerText = value;
        }} else {{
            const newElement = document.createElement('div');
            newElement.id = '{key}';
            newElement.innerText = value;
            document.body.appendChild(newElement);
        }}
    }}
    </script>
    """
    st.markdown(load_script, unsafe_allow_html=True)

if st.button('분석하기'):
    with st.spinner('분석 중입니다...'):
        video_urls = [video_url1, video_url2]
        analysis_texts = ["첫 번째 영상", "두 번째 영상"]
        analyses = []

        for i, url in enumerate(video_urls):
            video_id = get_video_id(url)
            if video_id:
                title, description = get_video_details(video_id)
                transcript = get_transcript(video_id)
                if transcript:
                    formatted_transcript = format_transcript(transcript)
                    truncated_transcript = truncate_text(formatted_transcript, max_length=4000)
                    transcript_text = f"{analysis_texts[i]} 분석\n\nTitle: {title}\n\nDescription: {description}\n\nTranscript: {truncated_transcript}\n\n"

                    analysis_prompt = f"""
                    {transcript_text}

                    Analyze the following aspects of the video:
                    1. Detailed content analysis
                    2. In-depth reasons for success
                    """

                    chat_completion = client.chat.completions.create(
                        messages=[
                            {
                                "role": "user",
                                "content": analysis_prompt,
                            },
                            {
                                "role": "system",
                                "content": "위 정보를 바탕으로 영상의 전체 내용과 영상이 성공한 이유를 작성해줘. 각 링크별로 분석해서 알려주는데 첫 번째 영상, 두 번째 영상이라고 꼭 표기해줘. 각 영상을 종합 분석한 후 3가지 추천 주제로 알려줘야 해. 답변은 한국어로 작성해줘.",
                            }
                        ],
                        model="gpt-4o",
                        max_tokens=4000
                    )

                    result = chat_completion.choices[0].message.content
                    analyses.append(result)
                    if i == 0:
                        st.session_state.analysis_1 = result
                    elif i == 1:
                        st.session_state.analysis_2 = result
                else:
                    st.warning(f"{analysis_texts[i]}에 대한 대본을 가져올 수 없습니다. 자막이 비활성화되어 있을 수 있습니다.")

        combined_analysis = "\n\n".join(analyses)
        if combined_analysis:
            recommendations_prompt = f"""
            {combined_analysis}

            종합 분석을 바탕으로, 적합한 숏폼 영상 주제를 3가지 추천해줘.
            """

            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": recommendations_prompt,
                    },
                    {
                        "role": "system",
                        "content": "위 정보를 바탕으로 종합 추천 주제를 한국어로 작성해줘.",
                    }
                ],
                model="gpt-4o",
                max_tokens=4000
            )

            recommendations_result = chat_completion.choices[0].message.content
            st.session_state.combined_recommendations = recommendations_result

if st.session_state.analysis_1:
    st.write(st.session_state.analysis_1)
    st.download_button(
        label="분석 결과 복사하기",
        data=st.session_state.analysis_1,
        file_name="analysis_1.txt"
    )

if st.session_state.analysis_2:
    st.write(st.session_state.analysis_2)
    st.download_button(
        label="분석 결과 복사하기",
        data=st.session_state.analysis_2,
        file_name="analysis_2.txt"
    )

if st.session_state.combined_recommendations:
    st.write("종합 추천 주제:\n")
    st.write(st.session_state.combined_recommendations)
    st.download_button(
        label="종합 추천 주제 복사하기",
        data=st.session_state.combined_recommendations,
        file_name="combined_recommendations.txt"
    )
    if st.button("저장하기: 종합 추천 주제"):
        save_to_local_storage("combined_recommendations", st.session_state.combined_recommendations)

if st.session_state.combined_recommendations:
    user_name = st.text_input("사용자 이름을 입력하세요")
    video_topic = st.text_input("숏폼 영상의 주제를 입력하세요")
    user_idea = st.text_input("당신의 아이디어를 입력하세요")
    target_audience = st.radio("타겟층을 선택하세요", ('20대', '30대', '40대'))

    if st.button('대본 생성'):
        script_prompt = f"""
        {st.session_state.analysis_1}

        {st.session_state.analysis_2}

        사용자 이름: {user_name}
        사용자의 아이디어: {user_idea}
        주제: {video_topic}
        타겟층: {target_audience}

        Based on the above analysis, create a short-form video script using the user's name and idea, tailored to the given topic and target audience.
        """

        script_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": script_prompt,
                },
                {
                    "role": "system",
                    "content": "위 정보를 바탕으로 1분 길이의 숏폼 영상의 대본을 작성해줘. 답변은 한국어로 작성해줘.",
                }
            ],
            model="gpt-4o",
            max_tokens=4000
        )

        script_result = script_completion.choices[0].message.content
        st.session_state.script_result = script_result

if st.session_state.script_result:
    st.write(st.session_state.script_result)
    st.download_button(
        label="대본 복사하기",
        data=st.session_state.script_result,
        file_name="script_result.txt"
    )
    if st.button("저장하기: 대본"):
        save_to_local_storage("script_result", st.session_state.script_result)

    if st.button('영상 제작'):
        production_prompt = f"""
        {st.session_state.script_result}

        Create a storyboard for this short-form video script. Include scene recommendations every 3 seconds, and suggest sound effects for each scene. The response should be in Korean.
        """

        production_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": production_prompt,
                },
                {
                    "role": "system",
                    "content": "위 정보를 바탕으로 3초마다 장면 추천 및 각 장면마다 효과음을 포함한 콘티를 작성해줘. 답변은 한국어로 작성해줘.",
                }
            ],
            model="gpt-4o",
            max_tokens=4000
        )

        production_result = production_completion.choices[0].message.content
        st.session_state.production_result = production_result

if st.session_state.production_result:
    st.write(st.session_state.production_result)
    st.download_button(
        label="영상 제작 콘티 복사하기",
        data=st.session_state.production_result,
        file_name="production_result.txt"
    )
    if st.button("저장하기: 영상 제작 콘티"):
        save_to_local_storage("production_result", st.session_state.production_result)

    if st.button('음악 생성'):
        music_prompt = f"""
        {st.session_state.production_result}

        Based on the storyboard, recommend 3 suitable background music tracks. Include the BPM and reasons for each recommendation. The response should be in Korean.
        """

        music_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": music_prompt,
                },
                {
                    "role": "system",
                    "content": "위 정보를 바탕으로 유튜브와 스포티 파이를 검색해서 3개의 적합한 배경 음악 트랙을 추천해줘. 각 음악의 BPM과 추천 이유를 알려줘. 답변은 한국어로 작성해줘",
                }
            ],
            model="gpt-4o",
            max_tokens=4000
        )

        music_result = music_completion.choices[0].message.content
        st.session_state.music_result = music_result

if st.session_state.music_result:
    st.write(st.session_state.music_result)
    st.download_button(
        label="음악 추천 복사하기",
        data=st.session_state.music_result,
        file_name="music_result.txt"
    )
    if st.button("저장하기: 음악 추천"):
        save_to_local_storage("music_result", st.session_state.music_result)

# 저장된 항목 보기
if st.sidebar.button("저장된 종합 추천 주제 보기"):
    new_window_script = """
    <script>
    window.open("", "_blank").document.write(localStorage.getItem("combined_recommendations"));
    </script>
    """
    st.sidebar.markdown(new_window_script, unsafe_allow_html=True)

if st.sidebar.button("저장된 대본 보기"):
    new_window_script = """
    <script>
    window.open("", "_blank").document.write(localStorage.getItem("script_result"));
    </script>
    """
    st.sidebar.markdown(new_window_script, unsafe_allow_html=True)

if st.sidebar.button("저장된 영상 제작 콘티 보기"):
    new_window_script = """
    <script>
    window.open("", "_blank").document.write(localStorage.getItem("production_result"));
    </script>
    """
    st.sidebar.markdown(new_window_script, unsafe_allow_html=True)

if st.sidebar.button("저장된 음악 추천 보기"):
    new_window_script = """
    <script>
    window.open("", "_blank").document.write(localStorage.getItem("music_result"));
    </script>
    """
    st.sidebar.markdown(new_window_script, unsafe_allow_html=True)

# 사이드바에 방문자 수 표시
st.sidebar.markdown("<h3 style='font-size:10px;'>방문자 수</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"<p style='font-size:10px;'>Today: {st.session_state['visitor_count']}</p>", unsafe_allow_html=True)
