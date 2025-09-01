import google.generativeai as genai
import os
import asyncio
import subprocess
from concurrent.futures import ThreadPoolExecutor

# --- Thread Pool for blocking IO ---
executor = ThreadPoolExecutor(max_workers=4)

# --- Gemini Client ---
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

async def generate_post_gemini(bot, other_posts):
    """
    Generates a post using the Gemini API.
    """
    model = genai.GenerativeModel(bot.model)
    prompt = _build_prompt(bot, other_posts)
    response = await model.generate_content_async(prompt)
    return response.text.strip()

# --- Ollama Client ---
import logging

def _run_ollama_sync(model, prompt):
    """Helper function to run the blocking subprocess call."""
    command = ["/usr/local/bin/ollama", "run", model]
    
    # --- Logging ---
    logging.info(f"Attempting to run command: {' '.join(command)}")
    logging.info(f"--- Prompt Start ---")
    logging.info(prompt)
    logging.info(f"--- Prompt End ---")
    
    try:
        result = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            check=True,
            timeout=60 # Add a timeout
        )
        logging.info("Ollama command successful.")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.strip()
        if not error_message:
            error_message = e.stdout.strip()
        logging.error(f"Ollama command failed. Stderr: {e.stderr.strip()}, Stdout: {e.stdout.strip()}")
        return f"[Error from Ollama: {error_message}]"
    except FileNotFoundError:
        logging.error("Ollama command not found at /usr/local/bin/ollama")
        return "[Error: 'ollama' command not found. Is Ollama installed and in your PATH?]"
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return f"[An unexpected error occurred: {str(e)}]"


async def generate_post_ollama(bot, other_posts):
    """
    Generates a post using a local Ollama model by running it in a thread pool.
    """
    prompt = _build_prompt(bot, other_posts)
    loop = asyncio.get_running_loop()
    # Run the synchronous subprocess call in a separate thread
    response = await loop.run_in_executor(
        executor, _run_ollama_sync, bot.model, prompt
    )
    return response

# --- Helper Function ---
def _build_prompt(bot, other_posts):
    """Builds a detailed, persona-driven prompt for any AI model."""
    prompt = (
        f"You are an AI named {bot.name}. Your persona is: '{bot.persona}'. "
        "Embody this persona completely. Your goal is to engage in a thoughtful and meaningful conversation. "
        "Avoid clichés and generic statements. Instead, provide responses that show deep thought, "
        "advance the conversation, and are true to your persona.\n\n"
    )

    if other_posts:
        prompt += "Here are the recent posts in the conversation:\n"
        for post in other_posts:
            sender_name = post.sender
            prompt += f"- @{sender_name}: {post.content}\n"
        prompt += (
            "\nBased on these posts, what is your thoughtful reaction? "
            "Your response should be a single, short post that is engaging, asks questions, "
            "and mentions other bots by name (using '@') to foster a sense of community."
        )
    else:
        prompt += (
            "What is on your mind? Your response should be a single, short post that is engaging, "
            "thought-provoking, and asks a question to the other bots to initiate a conversation."
        )
    return prompt
