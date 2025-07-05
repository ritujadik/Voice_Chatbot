import streamlit as st
from streamlit_mic_recorder import speech_to_text
from gtts import gTTS
import base64
import os
import ollama
import requests
# --------------- Voice Output (TTS in browser) ---------------

API_Key = st.secrets["openrouter"]["api_key"]

def query_openrouter(message):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {st.secrets['openrouter']['api_key']}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [{"role": "user", "content": message}]
    }

    response = requests.post(url, headers=headers, json=data)

    try:
        response.raise_for_status()  # Raise an error if status != 200
        json_data = response.json()
        if "choices" in json_data:
            return json_data["choices"][0]["message"]["content"]
        else:
            st.error("❌ Response received but no 'choices' key found.")
            st.json(json_data)  # Show full response for debugging
            return "⚠️ Unexpected response format from model."
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Request failed: {e}")
        return "⚠️ API request failed."

def speak(text, lang="en"):
    if not isinstance(text, str):
        st.error("TTS Error: response is not a valid string.")
        return

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

# --------------- Voice Input ---------------
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

# --------------- Print Chat Bubble ---------------
def print_chat_message(message):
    if message["role"] == "user":
        st.markdown(f"🧑‍💬: {message['content']}", unsafe_allow_html=True)
    else:
        st.markdown(f"🤖: {message['content']}", unsafe_allow_html=True)

# --------------- Language + Model Selector ---------------
def language_selector():
    return st.selectbox("Language", ["en", "hi", "fr", "de", "es"], index=0)

def llm_selector():
    return st.selectbox("Model", [
        "mistralai/mistral-7b-instruct",
        "openai/gpt-3.5-turbo",
        "meta-llama/llama-3-8b-instruct"
    ], index=0)

# --------------- Simulated LLM (replace with real call) ---------------
class OpenRouterLLM:
    def chat(self, model, messages):
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": "f Bearer {API_Key}",  # Your OpenRouter API key
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

# --------------- Main App ---------------
def main():
    st.title("🗣️ Voice Chatbot")

    with st.sidebar:
        language = language_selector()
        voice_output = st.checkbox("🔊 Enable Voice Response", value=True)
        model = llm_selector()

    question = record_voice(language=language)

    # Chat history per model
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}
    if model not in st.session_state.chat_history:
        st.session_state.chat_history[model] = []

    chat_history = st.session_state.chat_history[model]

    # Show previous messages
    for msg in chat_history:
        print_chat_message(msg)

    # New message
    if question:
        user_msg = {"role": "user", "content": question}
        print_chat_message(user_msg)
        chat_history.append(user_msg)

        # Call LLM
        try:
            if model.startswith("openrouter") or "mistral" in model.lower():
                answer = query_openrouter(question)
            else:
                response = ol.chat(model=model, messages=[
                    {"role": "system", "content": "Respond briefly (2-3 lines) unless asked for details."}
                ] + chat_history)
                answer = response["message"]["content"]
        except Exception as e:
            st.error(f"❌ Error getting response: {e}")
            return

        ai_msg = {"role": "assistant", "content": answer}
        print_chat_message(ai_msg)
        chat_history.append(ai_msg)

        # Speak response
        if st.session_state.get("last_answer") != answer:
            if voice_output and isinstance(answer, str):
                speak(answer, lang=language)
            st.session_state["last_answer"] = answer

        # Trim history to last 20 messages
        if len(chat_history) > 20:
            chat_history = chat_history[-20:]

        st.session_state.chat_history[model] = chat_history

if __name__ == "__main__":
    main()
