# Talk For Me - AI-Powered Conversation Assistant

A real-time conversation suggestion system that listens to conversations and generates contextual reply suggestions with different tones using local Ollama LLM.

## Features

- **Real-Time Listening**: Continuously listens to the other speaker
- **Smart Suggestions**: Generates 3+ contextual reply options
- **Tone Control**: Professional, Casual, Empathetic, Humorous
- **Conversation Context**: Remembers previous exchanges
- **Confidence Scoring**: Ranks suggestions by relevance
- **Local LLM**: Uses Ollama for privacy and offline operation

## Prerequisites

1. **Python 3.8+**
2. **Ollama** - Install and run locally:
   ```bash
   # Install Ollama from https://ollama.ai
   ollama serve
   ollama pull llama2
   ```
3. **PyAudio dependencies**:
   - **Windows**: PyAudio should install via pip
   - **Linux**: `sudo apt-get install portaudio19-dev python3-pyaudio`
   - **macOS**: `brew install portaudio`

## Installation

1. Clone the repository:
   ```bash
   cd d:\talkforme
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the application:
   ```bash
   # Copy environment template
   cp .env.example .env

   # Edit .env to configure Ollama settings (defaults should work)
   ```

4. Verify `config.json` settings match your needs

## Usage

1. **Start Ollama** (in a separate terminal):
   ```bash
   ollama serve
   ```

2. **Run Talk For Me**:
   ```bash
   python talk_for_me.py
   ```

3. **Start speaking** - The system will:
   - Listen for speech
   - Transcribe what it hears
   - Generate reply suggestions in different tones
   - Display suggestions with confidence scores

4. **Stop** with `Ctrl+C`

## Configuration

### Environment Variables (`.env`)

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
LOG_LEVEL=INFO
```

### Application Settings (`config.json`)

- **audio**: Configure microphone settings, VAD threshold, silence duration
- **llm**: Temperature, max tokens, number of suggestions
- **stt**: Language for speech recognition
- **conversation**: History size, auto-save settings
- **tones**: Which suggestion tones to generate
- **ui**: Display preferences

## Project Structure

```
talkforme/
├── talk_for_me.py              # Main application
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── config.json                 # App configuration
│
├── core/                       # Core business logic
│   ├── models.py               # Data models
│   ├── conversation_manager.py # History management
│   ├── suggestion_generator.py # LLM-based suggestions
│   └── audio_listener.py       # Audio processing
│
├── providers/                  # Provider implementations
│   ├── base/                   # Abstract interfaces
│   ├── llm/                    # Ollama LLM
│   ├── stt/                    # Speech Recognition
│   └── audio/                  # PyAudio
│
├── utils/                      # Utilities
│   ├── config_loader.py
│   └── logger.py
│
└── data/                       # Conversation history
```

## Troubleshooting

### Ollama Connection Issues
- Ensure Ollama is running: `ollama serve`
- Verify model is installed: `ollama list`
- Check URL in `.env` matches Ollama server

### Audio Issues
- Check available devices: Listed on startup
- Adjust `energy_threshold` in `config.json` if too sensitive/insensitive
- Ensure microphone permissions are granted

### Speech Recognition Issues
- Requires internet connection (uses Google Speech API free tier)
- Adjust `silence_duration` in `config.json` for faster/slower detection
- Check microphone input levels

## Advanced Configuration

### Using a Different Ollama Model

```bash
# Pull a different model
ollama pull mistral

# Update .env
OLLAMA_MODEL=mistral
```

### Adjusting Voice Activity Detection

Edit `config.json`:
```json
{
  "audio": {
    "energy_threshold": 4000,  // Lower = more sensitive
    "silence_duration": 1.5     // Seconds before ending speech
  }
}
```

### Customizing Suggestion Tones

Edit `config.json`:
```json
{
  "tones": [
    "professional",
    "casual",
    "empathetic",
    "humorous"
  ]
}
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please feel free to submit pull requests or open issues.
