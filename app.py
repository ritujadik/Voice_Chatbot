import streamlit as st
from streamlit_mic_recorder import speech_to_text
from gtts import gTTS
import base64
import os
import ollama
import requests
import re
from deep_translator import GoogleTranslator

API_Key = st.secrets["openrouter"]["api_key"]
model = ["meta-llama/llama-3-8b-instruct", "mistralai/mistral-7b-instruct"]

input_mode = "Type"


def clean_mixed_language_text(text, target_lang="hi"):
    fallback_words = {
        "kRgbuddy": "Connaught Place",
        "लाला कुलचNotifications": "Lala Kuan",
        "चोक डेव्बसन": "Chowk Davison",
        "नेशनल बिएन": "National Museum"
    }

    for bad, good in fallback_words.items():
        text = text.replace(bad, good)

    # Detect mixed script
    mixed_words = re.findall(r'\w*[^\u0900-\u097F\s][\u0900-\u097F]+\w*|\w*[\u0900-\u097F]+\w*[^\u0900-\u097F\s]', text)

    for word in mixed_words:
        try:
            translated = GoogleTranslator(source='auto', target='en').translate(word)
            text = text.replace(word, translated)
        except:
            text = text.replace(word, "[unreadable]")

    return text

def clean_hinglish_response(text):
    junk_patterns = [
        r'\balbidental\b', r'\bummedar\b', r'\bQayamat ke bicch\b',
        r'\bviral ticket\b', r'\bbrand-bottle\b', r'\bhapahap\b',
        r'\bmegha hain\b', r'\basar karo\b', r'\bkarqe mein\b',
        r'\bjakar dekhna pasandega achha\b'
    ]

    for pattern in junk_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Fix spacing, remove stray punctuations
    text = re.sub(r'\s{2,}', ' ', text).strip()
    return text


def query_openrouter(message):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {st.secrets['openrouter']['api_key']}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": message}]
    }

    response = requests.post(url, headers=headers, json=data)

    try:
        response.raise_for_status()
        json_data = response.json()
        if "choices" in json_data:
            return json_data["choices"][0]["message"]["content"]
        else:
            st.error("❌ Response received but no 'choices' key found.")
            st.json(json_data)
            return "⚠️ Unexpected response format from model."
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Request failed: {e}")
        return "⚠️ API request failed."

def speak(userinput, lang="en"):
    if not isinstance(userinput, str):
        st.error("TTS Error: response is not a valid string.")
        return

    # Remove known unwanted patterns or gibberish
    text = re.sub(r"\b(?:appendString|tarankan|[^\w\s\u0900-\u097F.,?!;:()])+\b", "", userinput)
    text = re.sub(r"\s{2,}", " ", text).strip()  # Clean up extra spaces

    tts = gTTS(text=text, lang=lang)
    tts.save("response.mp3")

    with open("response.mp3", "rb") as f:
        audio_data = f.read()
        b64 = base64.b64encode(audio_data).decode()

    audio_html = f"""
        <audio autoplay controls>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

def record_voice(language="en"):
    state = st.session_state
    if "text_received" not in state:
        state.text_received = []

    text = speech_to_text(
        start_prompt="🎤 Speak now...",
        stop_prompt="🛑 Listening...",
        language=language,
        use_container_width=True,
        just_once=True
    )

    if text:
        state.text_received.append(text)

    result = "".join(state.text_received)
    state.text_received = []

    return result if result else None

def print_chat_message(message):
    if message["role"] == "user":
        st.markdown(f"🧑‍💬: {message['content']}", unsafe_allow_html=True)
    else:
        st.markdown(f"🤖: {message['content']}", unsafe_allow_html=True)

def language_selector(model):
    model_lang_map = {
        "meta-llama/llama-3-8b-instruct": ["en", "hi", "fr", "de", "es"],
        "mistralai/mistral-7b-instruct": ["en", "hi", "fr", "de"],
    }
    supported = model_lang_map.get(model, ["en"])
    return st.selectbox("Answer Language", supported, index=0)

def llm_selector():
    return st.selectbox("Model", [
        "meta-llama/llama-3-8b-instruct",
        "mistralai/mistral-7b-instruct",
    ], index=0,key="llm_selector")

def get_language_name(code):
    return {
        "en": "English",
        "hi": "Hindi",
        "fr": "French",
        "de": "German",
        "es": "Spanish"
    }.get(code, "English")

class OpenRouterLLM:
    def chat(self, model, messages):
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {API_Key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": messages
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            print("❌ Error:", response.text)
            return {"message": {"content": "Error fetching response."}}

ol = OpenRouterLLM()
def main():
    st.title("🗣️ Voice Chatbot")

    with st.sidebar:
        llm_model = llm_selector()
        answer_lang = language_selector(llm_model)
        input_mode = st.radio("Input Mode", ["Chat", "Voice"])
        voice_output = st.checkbox("🔊 Enable Voice Response", value=True)

        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history[llm_model] = []

    # Initialize session state
    st.session_state.setdefault("chat_history", {})
    st.session_state.chat_history.setdefault(llm_model, [])
    chat_history = st.session_state.chat_history[llm_model]

    # 🗨️ Show all chat messages first
    for msg in chat_history:
        print_chat_message(msg)

    # 🧠 Handle user input after messages (fixed input area)
    question = None
    with st.container():
        if input_mode == "Chat":
            question = st.chat_input("Type your message here...")

        elif input_mode == "Voice":
            if "voice_input_ready" not in st.session_state:
                st.session_state.voice_input_ready = False

            if st.session_state.voice_input_ready:
                voice_text = record_voice(language="en")
                if voice_text:
                    st.session_state.voice_input_ready = False
                    question = voice_text
                else:
                    st.markdown("🎤 **Listening...**")
            else:
                if st.button("🎙️ Tap to Speak"):
                    st.session_state.voice_input_ready = True

    # 🧠 Process the message and respond
    if question:
        chat_history.append({"role": "user", "content": question})
        print_chat_message({"role": "user", "content": question})

        lang_name = get_language_name(answer_lang)
        system_prompt = {
            "role": "system",
            "content": (
                "Answer ONLY in Hinglish (Hindi using English letters). Keep it short and casual."
                if answer_lang == "hi"
                else f"Respond only in {lang_name}. Translate and reply in 2–3 short lines."
            )
        }

        try:
            response = ol.chat(model=llm_model, messages=[system_prompt] + chat_history)
            if "choices" in response and response["choices"]:
                answer = response["choices"][0]["message"]["content"]
            else:
                st.error("⚠️ Unexpected response format.")
                return
        except Exception as e:
            st.error(f"❌ Error getting response: {e}")
            return

        chat_history.append({"role": "assistant", "content": answer})
        print_chat_message({"role": "assistant", "content": answer})

        if voice_output:
            st.session_state["speak_text"] = answer
            st.session_state["speak_lang"] = answer_lang

        if len(chat_history) > 20:
            st.session_state.chat_history[llm_model] = chat_history[-20:]



if __name__ == "__main__":
    main()

    if "speak_text" in st.session_state:
        st.markdown("---")
        speak(
            st.session_state.pop("speak_text"),
            st.session_state.pop("speak_lang", "en")
        )

