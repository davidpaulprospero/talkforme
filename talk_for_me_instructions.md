# Talk For Me - AI-Powered Voice & Conversation Assistant

A comprehensive Python framework for automating voice interactions, generating real-time conversation suggestions, and managing communication workflows.

## 📋 Overview

"Talk For Me" is an AI-powered system designed to:
1. Listen to audio input/output
2. Generate intelligent reply suggestions based on conversation context
3. Convert text to speech (TTS)
4. Transcribe speech to text (STT)
5. Manage notes and conversation history
6. Operate locally using Ollama or connect to cloud APIs (OpenAI, ElevenLabs)

## 🏗️ System Architecture

This is a real-time conversation suggestion system focused on helping you reply to others during conversations.

### 📁 File Structure

```
talk-for-me/
├── talk_for_me.py          # Main application
├── providers/              # Concrete provider implementations
│   ├── base/               # Abstract base classes
│   ├── llm/                # Ollama / OpenAI
│   ├── stt/                # Whisper / Google / SpeechRecognition
│   ├── audio/              # PyAudio / SoundDevice
│   └── tts/                # ElevenLabs / Google (optional)
├── core/                   # Core business logic
│   ├── conversation_manager.py
│   ├── suggestion_generator.py
│   ├── audio_listener.py
│   └── models.py
├── utils/                  # Utilities
│   ├── config_loader.py
│   └── logger.py
└── data/                   # Storage for conversation history
    └── conversation_history.json
```

## 🚀 Key Features

- **Real-Time Listening**: Continuously listens to the other speaker
- **Smart Suggestions**: Generates 3+ contextual reply options
- **Tone Control**: Professional, Casual, Empathetic, Humorous
- **Conversation Context**: Remembers previous exchanges
- **Confidence Scoring**: Ranks suggestions by relevance
- **Auto-Read**: Optional TTS for suggestions (when implemented)

## 💻 Implementation Guide

To use this system, you need to implement the abstract provider classes. Here are the templates:

### 1. LLM Provider (Ollama)
```python
import requests

class OllamaLLMProvider(LLMProvider):
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False
        }
        response = requests.post(url, json=payload)
        return response.json()['response']
```

### 2. STT Provider (OpenAI Whisper)
```python
from openai import OpenAI

class OpenAIWhisperProvider(SpeechToTextProvider):
    def transcribe(self, audio_data: bytes) -> str:
        client = OpenAI(api_key=self.config.api_key)
        # Save audio_data to temp file first
        with open("temp.wav", "wb") as f:
            f.write(audio_data)
        
        with open("temp.wav", "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        return transcript.text
```

### 3. Audio Provider (PyAudio)
```python
import pyaudio
import wave

class PyAudioProcessor(AudioProcessor):
    def record_audio(self, duration: int) -> bytes:
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
        frames = []
        for _ in range(0, int(44100 / 1024 * duration)):
            data = stream.read(1024)
            frames.append(data)
        stream.stop_stream()
        stream.close()
        p.terminate()
        return b''.join(frames)
```

## 🛠️ Usage

```bash
python talk_for_me.py
```

## 📦 Requirements

- Python 3.8+
- `requests`
- `pyaudio` (for audio)
- `openai` (optional, for STT)
- `elevenlabs` (optional, for TTS)
- [Ollama](https://ollama.ai) (running locally for free LLM)
