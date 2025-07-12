# Voice_Chatbot
# 🗣️ Voice Chatbot using Streamlit + Ollama
A voice-based chatbot built with **Streamlit**, using voice input/output, and LLM responses from **Ollama (local)** or **OpenRouter (cloud)** models like Mistral.

## Features
- 🎤 Voice input (speech-to-text)
- 🤖 Local LLM chat with Ollama (e.g., LLaMA3, Mistral)
- ☁️ Fallback to OpenRouter's hosted models (like Mistral) for demo/testing
- 🔊 Voice output using gTTS
- 🧠 Chat history memory
## You can setup the project
 git clone https://github.com/ritujadik/Voice_Chatbot.git
cd Voice_Chatbot
## Create a virtual environment
python -m venv venv
source venv/Scripts/activate(for windows)
## Deployment Options
 if you want to run locally
 ### Install dependencies
 pip install -r requirements.txt

## Run Ollama (Install if not already)
Install ollama
ollama run mistral(start your desired model)

## Start the streamlit app
streamlit run app.py

## Deploy to Streamlit Cloud (No GPU required)
a)Push code to a GitHub repo.
 b)In app.py, set your OpenRouter API key:
    headers = {
     "Authorization": "Bearer sk-...",  # Replace with your OpenRouter API key
     "Content-Type": "application/json"
}
c)Add this key as a secret in Streamlit Cloud:
    Go to Settings > Secrets
    Add:OPENROUTER_API_KEY = "sk-..."
d) Update your code to read the key from secrets:
      import streamlit as st
      headers = {
          "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}",
          "Content-Type": "application/json"
}
streamlit
streamlit-mic-recorder
gtts
requests
ollama  # Only used locally


## Speak and chat away!

**Note** - We can choose the model selection using toggle for the below model like
mistral/mistral-7b-instruct
openai/gpt-3.5-turbo
meta-llama/llama-3-8b-instruct
## Configuration
The chatbot defaults to short 1–2 line responses for clarity. You can modify the generate_response() function in main.py to control tone or length.
## License
MIT License – feel free to modify and share!
## Feedback
Found a bug or have a suggestion? Open an issue or create a pull request!


