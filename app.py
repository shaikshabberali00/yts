import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from deep_translator import GoogleTranslator
from textblob import TextBlob
import re

st.title("YouTube Transcript Summarizer")

video_input = st.text_input("Enter YouTube Video ID or URL:")

# ---------------- Helper Functions ---------------- #
def extract_video_id(url_or_id: str) -> str:
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url_or_id)
    return match.group(1) if match else url_or_id

def batch_translate(lines, src_lang):
    batch_size = 5
    translated = []
    for i in range(0, len(lines), batch_size):
        chunk = " ".join(lines[i:i+batch_size])
        translated_text = GoogleTranslator(source=src_lang, target='en').translate(chunk)
        translated.append(translated_text)
    return translated

def grammar_fix(text):
    return str(TextBlob(text).correct())

# ---------------- Fetch & Translate ---------------- #
def fetch_translate_fix(video_id: str):
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        transcript = transcript_list.find_transcript([t.language_code for t in transcript_list])
        lang = transcript.language_code

        data = transcript.fetch()
        text_lines = [entry.text for entry in data]

        if lang != 'en':
            text_lines = batch_translate(text_lines, lang)
            lang = 'en (translated)'

        final_text = " ".join(text_lines)
        final_text = grammar_fix(final_text)
        return final_text, lang

    except VideoUnavailable:
        st.error("❌ Video not found or unavailable.")
    except TranscriptsDisabled:
        st.error("❌ Captions are disabled for this video.")
    except NoTranscriptFound:
        st.error("❌ No captions found for this video.")
    except Exception as e:
        st.error(f"⚠️ Unexpected error: {e}")
    return None, None

# ---------------- Main App ---------------- #
if video_input:
    video_id = extract_video_id(video_input)
    with st.spinner("Fetching, translating & improving subtitles..."):
        transcript, lang = fetch_translate_fix(video_id)

    if transcript:
        st.info(f"Subtitles fetched in language: **{lang}**")
        st.text_area("Enhanced Summary", transcript, height=400)
    else:
        st.info("No transcript available for this video.")
