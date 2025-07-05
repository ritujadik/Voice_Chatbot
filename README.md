# Voice_Chatbot
# 🗣️ Voice Chatbot using Streamlit + Ollama
A voice-enabled chatbot built with Python, Streamlit, and Ollama (local LLM), allowing real-time speech interaction and response directly in the browser—just like WhatsApp chat, but smarter.
## Features
- 🎤 Voice-to-text using OpenAI Whisper or browser microphone
- 🤖 AI responses using Ollama models (e.g., Mistral, LLaMa2)
- 🔊 Text-to-speech using gTTS (Google Text-to-Speech)
- 📦 Simple browser UI built with Streamlit
- 📱 Works like a real-time messaging app

## You can setup the project
 git clone https://github.com/ritujadik/Voice_Chatbot.git
cd Voice_Chatbot
## Create a virtual environment
python -m venv venv
source venv/Scripts/activate(for windows)
## Install dependencies
pip install -r requirements.txt

## Run Ollama (Install if not already)
Install ollama
ollama run mistral(start your desired model)

## Start the streamlit app
streamlit run app.py

## Speak and chat away!

**Note** - We can choose the model selection using toggle for the below model like
mistral
llama2
gemma
**Make sure the model is pulled in Ollama before use.**
## Configuration
The chatbot defaults to short 1–2 line responses for clarity. You can modify the generate_response() function in main.py to control tone or length.
## License
MIT License – feel free to modify and share!
## Feedback
Found a bug or have a suggestion? Open an issue or create a pull request!


