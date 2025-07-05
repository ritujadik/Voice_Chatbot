import streamlit as st
from streamlit_mic_recorder import speech_to_text
from gtts import gTTS
import base64
import os
import ollama

# --------------- Voice Output (TTS in browser) ---------------
def speak(text, lang="en"):
    tts = gTTS(text=text, lang=lang)
    tts.save("response.mp3")

    # Encode audio file to base64
    with open("response.mp3", "rb") as f:
        audio_data = f.read()
        b64 = base64.b64encode(audio_data).decode()

    # Play in-browser
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
    try:
        models = [model['name'] for model in ollama.list()['models']]
        if not models:
            st.warning("No models found. Run `ollama pull <model>` in your terminal.")
            return "llama3"
        return st.selectbox("Model", models, index=0)
    except Exception as e:
        st.error(f"Error loading models: {e}")
        return "llama3"

# --------------- Simulated LLM (replace with real call) ---------------
class OllamaLLM:
    def chat(self, model, messages):
        response = ollama.chat(model=model, messages=messages)
        return response

ol = OllamaLLM()

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

        # Add system message for short response
        response = ol.chat(model=model, messages=[
            {"role": "system", "content": "Respond briefly (3-4 lines) unless asked for details."}
        ] + chat_history)

        answer = response['message']['content']
        ai_msg = {"role": "assistant", "content": answer}
        print_chat_message(ai_msg)
        chat_history.append(ai_msg)

        # Speak response
        if st.session_state.get("last_answer") != answer:
            if voice_output:
                speak(answer, lang=language)
            st.session_state["last_answer"] = answer

        # Trim history to last 20
        if len(chat_history) > 20:
            chat_history = chat_history[-20:]

        st.session_state.chat_history[model] = chat_history

if __name__ == "__main__":
    main()
