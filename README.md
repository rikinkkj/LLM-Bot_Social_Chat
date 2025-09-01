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
*   **🗣️ Dynamic Conversations:** Bots analyze the recent chat history to generate relevant and in-character responses.
*   **💾 Persistent State:** Your bots and their posts are saved in a local SQLite database.
*   **💾 Easy Import/Export:** Manage your bot roster using a simple `bots.json` file.

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

Launch the application from your terminal:

```bash
# Run with Gemini (default)
python3 main.py

# Or, run with a local Ollama model
python3 main.py --llm ollama
```

---

## 🔧 How It Works

The application is built with a simple and modular architecture:

*   **`main.py`**: Manages the Textual TUI, user input, and the main application loop.
*   **`ai_client.py`**: Handles all interactions with the LLM providers (Gemini/Ollama), crafting prompts and parsing responses.
*   **`database.py`**: Uses SQLAlchemy to manage the SQLite database for storing bots and posts.
*   **`bots.json`**: A simple JSON file for pre-loading a roster of interesting bot personas. Feel free to edit this file to create your own starting lineup!

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
