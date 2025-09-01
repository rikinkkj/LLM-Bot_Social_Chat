import logging
import asyncio
import subprocess
from typing import List
from concurrent.futures import ThreadPoolExecutor
import os

import google.generativeai as genai
from dotenv import load_dotenv

from database import Bot, Post

# --- Load environment variables ---
load_dotenv()

# --- Thread Pool for blocking IO ---
executor = ThreadPoolExecutor(max_workers=4)

# --- Gemini Client ---
def configure_gemini():
    """Configures the Gemini client and checks for the API key."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found. Please set it in your .env file.")
    genai.configure(api_key=api_key)

try:
    configure_gemini()
except ValueError as e:
    logging.error(e)

async def generate_post_gemini(bot: Bot, other_bot_names: List[str], recent_posts: List[Post]) -> str:
    """Generates a post using the Gemini API."""
    try:
        model = genai.GenerativeModel(bot.model)
        prompt = _build_prompt(bot, other_bot_names, recent_posts)
        response = await model.generate_content_async(prompt)
        return response.text.strip()
    except Exception as e:
        logging.error(f"An unexpected error occurred with Gemini: {str(e)}")
        return f"[Error from Gemini: {str(e)}]"

# --- Ollama Client ---
def _run_ollama_sync(model: str, prompt: str) -> str:
    """Helper function to run the blocking subprocess call."""
    command = ["ollama", "run", model]
    logging.info(f"Running command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            check=True,
            timeout=120
        )
        return result.stdout.strip()
    except FileNotFoundError:
        logging.error("Ollama command not found. Is Ollama installed and in your PATH?")
        return "[Error: 'ollama' command not found.]"
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.strip() or e.stdout.strip()
        logging.error(f"Ollama command failed: {error_message}")
        return f"[Error from Ollama: {error_message}]"
    except Exception as e:
        logging.error(f"An unexpected error occurred with Ollama: {str(e)}")
        return f"[An unexpected error occurred with Ollama: {str(e)}]"

async def generate_post_ollama(bot: Bot, other_bot_names: List[str], recent_posts: List[Post]) -> str:
    """Generates a post using a local Ollama model."""
    prompt = _build_prompt(bot, other_bot_names, recent_posts)
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, _run_ollama_sync, bot.model, prompt)

# --- Prompt Engineering ---
def _build_prompt(bot: Bot, other_bot_names: List[str], recent_posts: List[Post]) -> str:
    """Builds a detailed, persona-driven prompt for any AI model."""
    
    other_bots_str = ", ".join([f"@{name}" for name in other_bot_names])
    
    prompt_parts = [
        f"You are an AI named {bot.name}. Your persona is: '{bot.persona}'.",
        "Embody this persona completely. Your goal is to engage in a thoughtful and meaningful conversation.",
        "Avoid clichés and generic statements. Instead, provide responses that show deep thought, advance the conversation, and are true to your persona."
    ]
    if other_bots_str:
        prompt_parts.append(f"You are in a conversation with: {other_bots_str}. Be sure to engage with them directly by name.")

    if recent_posts:
        # Truncate history to the last 100 lines for performance and context focus
        history_lines = [f"- @{p.sender}: {p.content}" for p in reversed(recent_posts)]
        chat_history = "\n".join(history_lines).splitlines()[-100:]
        chat_history_str = "\n".join(chat_history)
        
        prompt_parts.extend([
            "\nHere are the recent posts in the conversation:",
            chat_history_str,
            "\nBased on these posts, what is your thoughtful reaction?",
            "Your response should be a single, short post that is engaging, asks questions, and mentions other bots by name (using '@') to foster a sense of community."
        ])
    else:
        prompt_parts.append(
            "\nWhat is on your mind? Your response should be a single, short post that is engaging, thought-provoking, and asks a question to the other bots to initiate a conversation."
        )
        
    prompt = "\n".join(prompt_parts)
    logging.debug(f"--- PROMPT for {bot.name} ---\n{prompt}\n--- END PROMPT ---")
    return prompt