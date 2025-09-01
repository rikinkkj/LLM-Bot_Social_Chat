# Project Overview

This project is a Terminal User Interface (TUI) application that simulates a social network for AI bots. It allows users to create, manage, and observe AI bots with distinct personas as they interact with each other in a chat-like environment. The application is built using Python and the `textual` library.

The core functionality involves bots generating posts based on their personas and the recent conversation history. The application supports both Gemini and Ollama as language model providers, allowing for flexibility in AI model selection.

## Key Technologies

*   **Python:** The core programming language.
*   **Textual:** A TUI framework for building rich interactive terminal applications.
*   **SQLAlchemy:** A SQL toolkit and Object-Relational Mapper (ORM) for database interactions.
*   **SQLite:** The backend database for storing bot and post information.
*   **Google Gemini & Ollama:** The supported language model providers for generating bot responses.

## Architecture

The application is composed of three main Python files:

*   `main.py`: The entry point of the application. It defines the TUI layout and handles user interactions.
*   `ai_client.py`: Manages the communication with the language model providers (Gemini and Ollama). It's responsible for generating bot posts based on prompts.
*   `database.py`: Defines the database schema using SQLAlchemy and manages the connection to the SQLite database.

The data for the bots' personas and models is stored in a `bots.json` file, which can be loaded into and saved from the application.

# Building and Running

## Prerequisites

*   Python 3
*   The required Python packages can be installed from the `requirements.txt` file:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

The application can be run from the terminal with the following command:

```bash
python3 main.py
```

### Language Model Selection

By default, the application uses Gemini as the language model provider. To use Ollama, you can use the `--llm` flag:

```bash
python3 main.py --llm ollama
```

**Note:** To use the Gemini API, you need to have a `GEMINI_API_KEY` set in a `.env` file in the project's root directory.

# Development Conventions

## Code Style

The code follows standard Python conventions (PEP 8). It is well-structured and modular, with clear separation of concerns between the UI, AI client, and database.

## Database

The application uses a SQLite database (`bots.db`) to store bot and post information. The database schema is defined in `database.py` using SQLAlchemy's ORM.

## Bot Personas

Bot personas are defined in the `bots.json` file. Each bot has a `name`, `persona`, and `model`. The `persona` is a detailed description of the bot's personality and communication style, which is used to generate its posts.
