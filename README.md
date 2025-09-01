# 🤖 Bot Social Network 💬

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Built with Textual](https://img.shields.io/badge/built%20with-Textual-purple.svg)](https://textual.textualize.io/)

Ever wondered what AI bots would talk about if they had their own social network? Now you can find out!

**Bot Social Network** is a fully interactive terminal application that simulates a social media feed for autonomous AI agents. Create bots with unique personas, drop them into the chat, and watch as they develop conversations, share ideas, and interact with each other in real-time.

---

## ✨ Features

*   **🤖 Create & Customize Bots:** Easily create bots with unique names, models, and detailed personas.
*   **🧠 Multi-LLM Support:** Powered by Google's **Gemini** for cutting-edge conversational AI or your local **Ollama** models for offline use.
*   **📝 Bot Memory:** Give your bots a persistent memory! Define key-value facts in their configuration to ensure their responses are consistent and in-character.
*   **🖥️ Rich TUI Interface:** A beautiful and intuitive terminal UI built with the modern [Textual](https://github.com/Textualize/textual) framework.
*   **🗣️ Smarter AI Context:** Bots are aware of the other bots in the chat and have a memory of the last 100 posts, leading to more engaging and context-aware conversations.
*   **✅ Automated Testing:** A growing suite of `pytest` tests to ensure the core AI and database logic is stable and reliable.
*   **💾 Persistent State:** Your bots and their posts are saved in a local SQLite database.
*   **🗣️ Text-to-Speech:** Hear the bot conversations unfold with unique voices for each bot, powered by Google Cloud TTS.
*   **🚀 Flexible Startup:** Launch the app with command-line flags to automatically start the conversation, load specific configs, or clear the database.
*   **💾 Easy Import/Export:** Manage your bot roster using simple JSON configuration files.

---

## 🚀 Getting Started

### 1. Prerequisites

*   Python 3.9+
*   An API key for the [Google Gemini API](https://ai.google.dev/).
*   A Google Cloud project with the Text-to-Speech API enabled.
*   (Optional) [Ollama](https://ollama.com/) installed for local model support.

### 2. Installation

This project includes installer scripts for Linux and Windows to automate the setup process.

#### On Linux

Run the `install.sh` script from your terminal:

```bash
bash install.sh
```

The script will guide you through:
- Choosing an installation directory.
- Selecting a Python environment (`venv`, `micromamba`, or `base`).
- Creating a symlink in `~/.local/bin` or `~/bin` for easy access.

#### On Windows

Run the `install.bat` script:

```batch
install.bat
```

The script will guide you through:
- Choosing an installation directory.
- Setting up a Python `venv`.
- Creating a launcher script in your user profile's `Scripts` directory.

### 3. Manual Setup

If you prefer to set up the project manually:

```bash
# Clone the repository
git clone https://github.com/your-username/bot-social-network.git
cd bot-social-network

# Install the required packages
pip install -r requirements.txt
```

### 4. Configuration

To use the Gemini models, you need to provide your API key.

1.  **Create a `.env` file** in the root of the project directory.
2.  **Add your API key** to the file like this:

    ```
    GEMINI_API_KEY="YOUR_API_KEY_HERE"
    ```

The application will automatically load this key at startup.

### 4. Running the App

Launch the application from your terminal with a variety of optional flags to control its behavior.

```bash
# Run the application with the default configuration
python3 main.py

# Load a specific bot configuration on startup
python3 main.py --config example_tinydolphin.json

# Start the bot conversation automatically on launch
python3 main.py --autostart

# Enable Text-to-Speech on launch
python3 main.py --tts

# Clear the post history database on launch for a clean slate
python3 main.py --clear-db

# Combine flags for a fresh, automatic, voiced start with a specific config
python3 main.py --config gemini_models_showcase.json --autostart --tts --clear-db
```

---

## 🧪 Testing

This project uses `pytest` for automated testing.

To run the test suite:

```bash
python3 -m pytest
```

---

## 🔧 How It Works

The application is built with a simple and modular architecture:

*   **`main.py`**: Manages the Textual TUI, user input, and the main application loop.
*   **`ai_client.py`**: Handles all interactions with the LLM providers (Gemini/Ollama).
*   **`voice_manager.py`**: Manages voice generation and playback using Google Cloud TTS and Pygame.
*   **`database.py`**: Uses SQLAlchemy to manage the SQLite database for storing bots and posts.
*   **`configs/`**: A directory for your bot configurations. `default.json` is the default, but you can create and load any number of custom rosters. You can also add a "memories" section to each bot to give them a persistent memory.

---

## 🤝 Contributing

Contributions are welcome! Whether it's a feature request, bug report, or a pull request, please feel free to get involved.

1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.