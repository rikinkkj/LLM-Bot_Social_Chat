import os
import sys
import tempfile
import asyncio
import logging
from typing import List, Dict, Optional

from google.api_core import exceptions
from google.cloud import texttospeech

# Silence the pygame community welcome message
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
import pygame

# --- Globals ---
_voice_cache: Dict[str, List[str]] = {"male": [], "female": []}

# --- Core Functions ---

def get_voices() -> Dict[str, List[str]]:
    """
    Fetches and caches a list of available 'en-US' "Chirp3" voices, categorized by gender.
    Returns the cached list if already populated.
    """
    if _voice_cache.get("male") or _voice_cache.get("female"):
        return _voice_cache

    print("Fetching available voices from Google Cloud...", file=sys.stderr)
    try:
        client = texttospeech.TextToSpeechClient()
        voices_response = client.list_voices(language_code="en-US")
        
        for voice in voices_response.voices:
            if "Chirp3" in voice.name:
                gender = texttospeech.SsmlVoiceGender(voice.ssml_gender).name.lower()
                if gender in _voice_cache:
                    _voice_cache[gender].append(voice.name)
        
        logging.info(f"Loaded {_voice_cache['male']} male and {_voice_cache['female']} female voices.")
        return _voice_cache

    except exceptions.GoogleAPICallError as e:
        logging.error(f"Error fetching voice list from Google Cloud: {e}")
        logging.error("Please ensure you are authenticated. Try running 'gcloud auth application-default login'")
        return {"male": [], "female": []}

def select_voice(bot_name: str) -> Optional[str]:
    """Selects a voice for a bot based on a hash of its name."""
    if not _voice_cache["male"] and not _voice_cache["female"]:
        logging.warning("No voices loaded, cannot select a voice.")
        return None

    # Determine gender based on hash of bot name
    if hash(bot_name) % 2 == 0:
        gender_voices = _voice_cache["female"]
        if not gender_voices: # Fallback to male if no female voices
            gender_voices = _voice_cache["male"]
    else:
        gender_voices = _voice_cache["male"]
        if not gender_voices: # Fallback to female if no male voices
            gender_voices = _voice_cache["female"]
            
    if not gender_voices:
        return None

    # Select voice from the chosen gender list
    voice_index = hash(bot_name) % len(gender_voices)
    return gender_voices[voice_index]

async def generate_voice_data(text: str, voice_name: str) -> Optional[bytes]:
    """Generates speech from text and returns the audio content as bytes."""
    try:
        client = texttospeech.TextToSpeechAsyncClient()
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(language_code="en-US", name=voice_name)
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

        response = await client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        return response.audio_content

    except exceptions.GoogleAPICallError as e:
        logging.error(f"Error during speech synthesis: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred in voice generation: {e}")
    return None

def play_audio_data(audio_data: bytes):
    """Plays audio data from bytes using pygame."""
    try:
        pygame.mixer.init()
        # Use a temporary file in memory to play the audio
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as temp_audio_file:
            temp_audio_file.write(audio_data)
            temp_audio_file.flush() # Ensure all data is written
            
            pygame.mixer.music.load(temp_audio_file.name)
            pygame.mixer.music.play()
            # The waiting will be handled by the caller
            
    except Exception as e:
        logging.error(f"Error playing audio: {e}")

def stop_audio():
    """Stops any currently playing audio."""
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()
        pygame.mixer.quit()
