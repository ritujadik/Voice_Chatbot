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
        "google/gemma-7b-it": ["en"]
    }
    supported = model_lang_map.get(model, ["en"])
    return st.selectbox("Answer Language", supported, index=0)

def llm_selector():
    return st.selectbox("Model", [
        "meta-llama/llama-3-8b-instruct",
        "mistralai/mistral-7b-instruct",
        "google/gemma-7b-it"
    ], index=0)

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
        model = llm_selector()
        language = language_selector(model)
        voice_output = st.checkbox("🔊 Enable Voice Response", value=True)
        input_mode = st.radio("Select Input Mode", ("🎙️ Voice", "⌨️ Type"))

        if st.button("🗑️ Clear Chat History"):
            if "chat_history" in st.session_state:
                st.session_state.chat_history[model] = []

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}
    if model not in st.session_state.chat_history:
        st.session_state.chat_history[model] = []

    chat_history = st.session_state.chat_history[model]

    # Display chat history
    for msg in chat_history:
        print_chat_message(msg)

    # Get input from user
    question = None
    if input_mode == "🎙️ Voice":
        st.write("🎤 Listening...")
        question = record_voice(language="en")  # Always record in English
    else:
        user_input = st.text_input("Type your message:")
        if st.button("Submit") and user_input:
            question = user_input

    # If question exists, process it
    if question:
        user_msg = {"role": "user", "content": question}
        print_chat_message(user_msg)
        chat_history.append(user_msg)

        try:
            output_language_name = get_language_name(language)

            if language == "hi":
                system_prompt = {
                    "role": "system",
                    "content": (
                        "Answer ONLY in Hinglish (Hindi written using English letters). Do NOT use Hindi script. "
                        "Do NOT mix with other languages like Spanish, French, or gibberish tokens. "
                        "Avoid hallucinated or corrupted words like 'hathitग' or similar. "
                        "Use short 2-3 line casual answers, in bullet points if needed.\n\n"
                        "Examples:\n"
                        "- Taj Mahal Agra mein hai\n"
                        "- Agra ka Petha bahut famous hai\n"
                        "- Fatehpur Sikri bhi nearby ek historical jagah hai"
                    )
                }
            else:
                system_prompt = {
                    "role": "system",
                    "content": (
                        f"Respond only in {output_language_name}. "
                        f"Translate user's English input to {output_language_name} and give a short, helpful reply in 2-3 lines. "
                        f"Do not mix languages. Do not explain language mismatch."
                    )
                }

            response = ol.chat(model=model, messages=[system_prompt] + chat_history)

            if "choices" in response and response["choices"]:
                answer = response["choices"][0]["message"]["content"]
            else:
                st.error("❌ Unexpected response format.")
                st.json(response)
                return

        except Exception as e:
            st.error(f"❌ Error getting response: {e}")
            return

        ai_msg = {"role": "assistant", "content": answer}
        print_chat_message(ai_msg)
        chat_history.append(ai_msg)

        if voice_output and isinstance(answer, str):
            speak(answer, lang=language)

        if len(chat_history) > 20:
            chat_history = chat_history[-20:]

        st.session_state.chat_history[model] = chat_history


if __name__ == "__main__":
    main()

