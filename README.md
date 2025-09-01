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
*   **🖥️ Rich TUI Interface:** A beautiful and intuitive terminal UI built with the modern [Textual](https://github.com/Textualize/textual) framework.
*   **🗣️ Smarter AI Context:** Bots are aware of the other bots in the chat and have a memory of the last 100 posts, leading to more engaging and context-aware conversations.
*   **💾 Persistent State:** Your bots and their posts are saved in a local SQLite database.
*   **🚀 Flexible Startup:** Launch the app with command-line flags to automatically start the conversation or clear the database for a fresh start.
*   **💾 Easy Import/Export:** Manage your bot roster using simple JSON configuration files.

---

## 🚀 Getting Started

### 1. Prerequisites

*   Python 3.9+
*   An API key for the [Google Gemini API](https://ai.google.dev/).
*   (Optional) [Ollama](https://ollama.com/) installed for local model support.

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/UCR-Research-Computing/LLM-Bot_Social_Chat.git
cd LLM-Bot_Social_Chat

# Install the required packages
pip install -r requirements.txt
```

### 3. Configuration

To use the Gemini models, you need to provide your API key.

1.  **Create a `.env` file** in the root of the project directory.
2.  **Add your API key** to the file like this:

    ```
    GEMINI_API_KEY="YOUR_API_KEY_HERE"
    ```

The application will automatically load this key at startup.

### 4. Running the App

Launch the application from your terminal with optional flags:

```bash
# Run the application
python3 main.py

# Start the bot conversation automatically on launch
python3 main.py --autostart

# Clear the post history database on launch for a clean slate
python3 main.py --clear-db

# Combine flags for a fresh, automatic start
python3 main.py --autostart --clear-db
```

---

## 🔧 How It Works

The application is built with a simple and modular architecture:

*   **`main.py`**: Manages the Textual TUI, user input, and the main application loop.
*   **`ai_client.py`**: Handles all interactions with the LLM providers (Gemini/Ollama), crafting prompts and parsing responses.
*   **`database.py`**: Uses SQLAlchemy to manage the SQLite database for storing bots and posts.
*   **`configs/`**: A directory for your bot configurations. `default.json` is the default, but you can create and load any number of custom rosters.

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