import os
import re
import streamlit as st
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
import requests
from urllib.parse import urlparse, parse_qs

custom_css = """
    <style>
        /* 전체 body에 대한 스타일 */
        body {
            font-family: Georgia, serif;
        }
        /* 특정 요소에 대한 스타일 */
        .title {
            font-size: 240px;
        }
        .centered-text {
            text-align: center;
            background-color: #f0f0f0;
            color: #333;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# API 키 설정
os.environ["OPENAI_API_KEY"] = st.secrets['API_KEY']['OPENAI_API_KEY']
os.environ["YOUTUBE_API_KEY"] = st.secrets['YOUTUBE_API_KEY']['YOUTUBE_API_KEY']
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

image_url = "CREATIVE2.png" 
st.image(image_url, use_column_width=True)


st.markdown("<div style='text-align: center;'><h1>CREATIVE<h1></div>", unsafe_allow_html=True)

st.markdown("<div style='text-align: center; font-size: 100px; font-family: Georgia, serif'>CREATIVE</div>", unsafe_allow_html=True)

st.markdown("<div class='centered-text'>CREATIVE</div>", unsafe_allow_html=True)

st.markdown("---", unsafe_allow_html=True)

def main():
    st.title("Copy Paste in streamlit")
    pathinput = st.text_input("Enter your Path:")
    #you can place your path instead
    Path = f'''{pathinput}'''
    st.code(Path, language="python")
    st.markdown("Now you get option to copy")
if __name__ == "__main__":main()



video_url1 = st.text_input("첫 번째 YouTube 영상 URL을 입력하세요")
video_url2 = st.text_input("두 번째 YouTube 영상 URL을 입력하세요")
video_url3 = st.text_input("세 번째 YouTube 영상 URL을 입력하세요")

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
    response = requests.get(url)
    if response.status_code == 200:
        video_info = response.json()
        if 'items' in video_info and len(video_info['items']) > 0:
            title = video_info['items'][0]['snippet']['title']
            description = video_info['items'][0]['snippet']['description']
            return title, description
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

if 'combined_analysis' not in st.session_state:
    st.session_state.combined_analysis = ""

if st.button('분석하기'):
    with st.spinner('분석 중입니다...'):
        video_urls = [video_url1, video_url2, video_url3]
        combined_analysis = ""

        for url in video_urls:
            video_id = get_video_id(url)
            if video_id:
                title, description = get_video_details(video_id)
                transcript = get_transcript(video_id)
                if transcript:
                    formatted_transcript = format_transcript(transcript)
                    truncated_transcript = truncate_text(formatted_transcript, max_length=4000)
                    transcript_text = f"Title: {title}\n\nDescription: {description}\n\nTranscript: {truncated_transcript}\n\n"
                    combined_analysis += transcript_text
                else:
                    st.warning(f"비디오 ID {video_id}에 대한 대본을 가져올 수 없습니다. 자막이 비활성화되어 있을 수 있습니다.")

        if combined_analysis:
            truncated_analysis = truncate_text(combined_analysis, max_length=4000)
            analysis_prompt = f"""
            Combined Analysis of the Videos:

            {truncated_analysis}

            Analyze the following aspects of the combined videos:
            1. Detailed content analysis
            2. In-depth reasons for success
            3. Recommended video topics based on this content (2 topics)
            """

            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": analysis_prompt,
                    },
                    {
                        "role": "system",
                        "content": "위 정보를 바탕으로 1분 길이의 숏폼 영상의 전체 내용, 영상이 성공한 이유, 이 내용을 바탕으로 추가로 다룰 수 있는 추천 주제 2개를 작성해줘. 답변은 한국어로 작성해줘.",
                    }
                ],
                model="gpt-4",
                max_tokens=4000
            )

            result = chat_completion.choices[0].message.content
            st.session_state.combined_analysis = result
            st.write(result)
        else:
            st.error("자막을 사용할 수 있는 비디오가 없습니다. 유효한 비디오 URL을 입력하세요.")

if st.session_state.combined_analysis:
    user_name = st.text_input("사용자 이름을 입력하세요")
    video_topic = st.text_input("숏폼 영상의 주제를 입력하세요")
    user_idea = st.text_input("당신의 아이디어를 입력하세요")
    target_audience = st.radio("타겟층을 선택하세요", ('20대', '30대', '40대'))

    if st.button('대본 생성'):
        script_prompt = f"""
        {st.session_state.combined_analysis}

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
            model="gpt-4",
            max_tokens=4000
        )

        script_result = script_completion.choices[0].message.content
        st.write(script_result)
