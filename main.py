import json
import argparse
import random
import logging
import asyncio
import subprocess
import os
from typing import Optional, List, Tuple

from textual.app import App, ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Header, Footer, ListView, ListItem, Label, Input, Button, Static, TextArea, Select
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.binding import Binding

from database import Bot, Post, Memory, session, close_database_connection, clear_posts_table
import ai_client
import voice_manager

# --- Helper Functions ---

def _parse_memory_string(memory_string: Optional[str]) -> Optional[Tuple[str, str]]:
    """Parses a 'key: value' string into a tuple, handling errors."""
    if not memory_string or memory_string.lower().strip() == "none" or ":" not in memory_string:
        return None
    try:
        key, value = memory_string.split(":", 1)
        return key.strip(), value.strip()
    except ValueError:
        return None

# --- Model Loading ---

def get_available_models() -> List[Tuple[str, str]]:
    """Gets a list of available models from Gemini and Ollama."""
    
    gemini_models = [
        ("Gemini 1.5 Flash", "gemini-1.5-flash"),
        ("Gemini 1.5 Pro", "gemini-1.5-pro"),
        ("Gemini 2.5 Flash", "gemini-2.5-flash"),
        ("Gemini 2.5 Pro", "gemini-2.5-pro"),
    ]

    ollama_models = []
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            for line in lines[1:]:
                parts = line.split()
                if parts:
                    model_name = parts[0].split(':')[0]
                    ollama_models.append((model_name, model_name))
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        logging.warning(f"Could not list Ollama models: {e}")

    return gemini_models + ollama_models

# --- Logging Setup ---
logging.basicConfig(
    level="DEBUG",
    filename="bots.log",
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Screens ---

class SaveConfigScreen(ModalScreen[str]):
    """A modal screen for saving a bot configuration."""

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="dialog"):
            yield Label("Save Bot Configuration")
            yield Input(placeholder="Filename (e.g., my_team)", id="config_name")
            with Horizontal(id="buttons"):
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss()
        elif event.button.id == "save":
            filename = self.query_one("#config_name", Input).value
            if filename:
                self.dismiss(filename)

class LoadConfigScreen(ModalScreen[str]):
    """A modal screen for loading a bot configuration."""

    def __init__(self, config_files: List[str]):
        super().__init__()
        self.config_files = config_files

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="dialog"):
            yield Label("Load Bot Configuration")
            if self.config_files:
                yield Select([(f, f) for f in self.config_files], prompt="Select a file", id="config_select")
            else:
                yield Label("No configuration files found in 'configs/' directory.")
            with Horizontal(id="buttons"):
                yield Button("Load", variant="primary", id="load")
                yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss()
        elif event.button.id == "load":
            select = self.query_one(Select)
            if select.value:
                self.dismiss(select.value)

class BotEditScreen(ModalScreen[dict]):
    """A modal screen for creating or editing a bot."""

    def __init__(self, bot_to_edit: Optional[Bot] = None, available_models: List[Tuple[str, str]] = []):
        super().__init__()
        self.bot_to_edit = bot_to_edit
        self.available_models = available_models

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="dialog"):
            yield Label("Edit Bot" if self.bot_to_edit else "Create New Bot")
            yield Input(
                value=self.bot_to_edit.name if self.bot_to_edit else "",
                placeholder="Name",
                id="bot_name"
            )
            yield TextArea(
                text=self.bot_to_edit.persona if self.bot_to_edit else "",
                id="bot_persona"
            )
            # Determine the initial value for the Select widget
            initial_model = None
            if self.bot_to_edit:
                initial_model = self.bot_to_edit.model
            elif self.available_models:
                initial_model = self.available_models[0][1]

            yield Select(
                self.available_models,
                value=initial_model,
                prompt="Select model",
                id="bot_model",
                allow_blank=False if self.available_models else True,
            )
            with Horizontal(id="buttons"):
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss()
        elif event.button.id == "save":
            bot_data = {
                "name": self.query_one("#bot_name", Input).value,
                "persona": self.query_one("#bot_persona", TextArea).text,
                "model": self.query_one("#bot_model", Select).value,
            }
            if all(bot_data.values()):
                self.dismiss(bot_data)

# --- Widgets ---

class BotManager(ListView):
    """Widget to display and manage the list of bots."""
    def on_mount(self) -> None:
        self.border_title = "Bots"
        self.app.run_task(self.refresh_bots())

    async def refresh_bots(self):
        def _get_bots() -> List[Bot]:
            return session.query(Bot).all()
        bots = await asyncio.to_thread(_get_bots)
        self.app.bot_names = [bot.name for bot in bots]
        self.clear()
        for bot in bots:
            self.append(ListItem(Label(bot.name)))

class PostView(ListView):
    """Widget to display the chat history."""
    def on_mount(self) -> None:
        self.border_title = "Posts"
        self.app.run_task(self.refresh_posts())

    def add_post(self, post: Post):
        sender = post.sender or (post.bot.name if post.bot else "Unknown")
        self.mount(ListItem(Static(f"{sender}: {post.content}")), before=0)
        self.scroll_home(animate=False)

    async def refresh_posts(self):
        def _get_posts() -> List[Post]:
            return session.query(Post).order_by(Post.id.desc()).all()
        posts = await asyncio.to_thread(_get_posts)
        self.clear()
        for post in reversed(posts): # Display in chronological order
            self.add_post(post)

# --- Main App ---

class BotSocialApp(App):
    CSS_PATH = "style.css"
    BINDINGS = [Binding("q", "quit", "Quit")]

    def __init__(self, config_file: str = "default.json", autostart: bool = False, clear_db: bool = False, autostart_tts: bool = False):
        super().__init__()
        self.config_file = config_file
        self.autostart = autostart
        self.tts_enabled = autostart_tts
        self.tts_queue = asyncio.Queue(maxsize=1)
        if clear_db:
            clear_posts_table()
        self.background_tasks = set()
        self.selected_bot: Optional[Bot] = None
        self.available_models = get_available_models()
        self.bot_names: List[str] = []
        logging.info("Application started.")

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Vertical(
                BotManager(),
                Horizontal(Button("Create Bot", id="create_bot"), Button("Edit Bot", id="edit_bot")),
                Button("Delete Bot", id="delete_bot"),
                Horizontal(Button("Load Config", id="load_bots"), Button("Save Config", id="save_bots")),
                id="left-pane"
            ),
            Vertical(
                PostView(),
                Horizontal(Button("Start", id="start_chat"), Button("Stop", id="stop_chat"), Button("Clear", id="clear_chat")),
                Horizontal(Input(placeholder="Topic", id="topic_input"), Button("Inject Topic", id="inject_topic")),
                Button("TTS: ON" if self.tts_enabled else "TTS: OFF", id="toggle_tts"),
                id="right-pane"
            )
        )
        yield Footer()

    def on_mount(self) -> None:
        self.run_task(self.initialize_voices())
        self.run_task(self.load_bots_from_json(self.config_file))
        self.run_task(self.speaker_worker())
        self.bot_timer = self.set_interval(15, self.run_bot_activity, pause=not self.autostart)

    async def initialize_voices(self):
        """Initializes the voice cache."""
        await asyncio.to_thread(voice_manager.get_voices)

    def run_task(self, coro):
        task = asyncio.create_task(coro)
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

    # --- Event Handlers ---

    def on_list_view_selected(self, event: ListView.Selected):
        if isinstance(event.list_view, BotManager):
            bot_name = event.item.children[0].renderable
            self.run_task(self.select_bot_by_name(str(bot_name)))
    
    async def select_bot_by_name(self, name: str):
        def _get_bot():
            return session.query(Bot).filter_by(name=name).first()
        self.selected_bot = await asyncio.to_thread(_get_bot)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "topic_input" and event.value:
            await self.action_inject_topic(event.value)
            event.input.value = ""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create_bot":
            self.selected_bot = None
            self.push_screen(BotEditScreen(available_models=self.available_models), self.handle_bot_edit_result)
        elif event.button.id == "edit_bot":
            if self.selected_bot:
                self.push_screen(BotEditScreen(bot_to_edit=self.selected_bot, available_models=self.available_models), self.handle_bot_edit_result)
        elif event.button.id == "delete_bot":
            if self.selected_bot:
                self.run_task(self.action_delete_bot())
        elif event.button.id == "load_bots":
            self.push_screen(LoadConfigScreen(config_files=self.get_config_files()), self.handle_load_config)
        elif event.button.id == "save_bots":
            self.push_screen(SaveConfigScreen(), self.handle_save_config)
        elif event.button.id == "start_chat":
            self.bot_timer.resume()
        elif event.button.id == "stop_chat":
            self.bot_timer.pause()
        elif event.button.id == "clear_chat":
            self.run_task(self.action_clear_posts())
        elif event.button.id == "inject_topic":
            topic_input = self.query_one("#topic_input", Input)
            if topic_input.value:
                self.run_task(self.action_inject_topic(topic_input.value))
                topic_input.value = ""
        elif event.button.id == "toggle_tts":
            self.tts_enabled = not self.tts_enabled
            event.button.label = f"TTS: {'ON' if self.tts_enabled else 'OFF'}"

    # --- Action & Callback Methods ---

    def handle_bot_edit_result(self, bot_data: Optional[dict]):
        if bot_data:
            task = self.action_edit_bot(bot_data) if self.selected_bot else self.action_create_bot(bot_data)
            self.run_task(task)

    def handle_save_config(self, filename: Optional[str]):
        if filename:
            self.run_task(self.save_bots_to_json(filename))

    def handle_load_config(self, filename: Optional[str]):
        if filename:
            self.run_task(self.load_bots_from_json(filename))

    async def run_bot_activity(self):
        bots = await asyncio.to_thread(session.query(Bot).all)
        if not bots:
            return

        bot_to_post = random.choice(bots)
        other_bot_names = [b.name for b in bots if b.name != bot_to_post.name]
        
        recent_posts = await asyncio.to_thread(
            session.query(Post).order_by(Post.id.desc()).limit(50).all
        )
        
        memories = await asyncio.to_thread(
            session.query(Memory).filter_by(bot_id=bot_to_post.id).all
        )

        post_content = ""
        try:
            if bot_to_post.model.startswith("gemini"):
                post_content = await ai_client.generate_post_gemini(bot_to_post, other_bot_names, recent_posts, memories)
            else:
                post_content = await ai_client.generate_post_ollama(bot_to_post, other_bot_names, recent_posts, memories)
        except Exception as e:
            post_content = f"[SYSTEM Error: {e}]"

        sender_name = "SYSTEM" if post_content.startswith(("[Error", "[SYSTEM")) else bot_to_post.name
        new_post = await asyncio.to_thread(self.create_post, post_content, sender_name, bot_to_post)

        if self.tts_enabled and not post_content.startswith("[SYSTEM"):
            voice_name = voice_manager.select_voice(bot_to_post.name)
            if voice_name:
                audio_data = await voice_manager.generate_voice_data(post_content, voice_name)
                if audio_data:
                    await self.tts_queue.put({"audio": audio_data, "post": new_post})
        else:
            self.query_one(PostView).add_post(new_post)
        
        # After posting, try to form a new memory
        self.run_task(self.form_new_memory(bot_to_post))

    async def speaker_worker(self):
        """The consumer task that plays audio from the queue."""
        while True:
            data = await self.tts_queue.get()
            post = data["post"]
            audio = data["audio"]
            
            self.query_one(PostView).add_post(post)
            await asyncio.to_thread(voice_manager.play_audio_data, audio)
            
            # Wait for the audio to finish playing without blocking
            while voice_manager.pygame.mixer.get_init() and voice_manager.pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)

            self.tts_queue.task_done()

    async def form_new_memory(self, bot: Bot):
        """Asks the AI to generate a new memory and saves it to the database."""
        recent_posts = await asyncio.to_thread(
            session.query(Post).order_by(Post.id.desc()).limit(5).all
        )
        
        new_memory_str = await ai_client.generate_new_memory(bot, recent_posts)
        
        parsed_memory = _parse_memory_string(new_memory_str)
        if parsed_memory:
            key, value = parsed_memory
            new_memory = Memory(key=key, value=value, bot=bot)
            await asyncio.to_thread(self.db_add_memory, new_memory)
            logging.info(f"New memory for {bot.name}: {key} = {value}")
        else:
            logging.info(f"No new memory formed for {bot.name}.")

    # --- Core Actions ---

    async def action_create_bot(self, bot_data: dict):
        await asyncio.to_thread(self.db_create_bot, **bot_data)
        await self.query_one(BotManager).refresh_bots()

    async def action_edit_bot(self, bot_data: dict):
        await asyncio.to_thread(self.db_edit_bot, self.selected_bot, **bot_data)
        await self.query_one(BotManager).refresh_bots()

    async def action_delete_bot(self):
        await asyncio.to_thread(self.db_delete_bot, self.selected_bot)
        self.selected_bot = None
        await self.query_one(BotManager).refresh_bots()

    async def action_clear_posts(self):
        await asyncio.to_thread(self.db_clear_posts)
        await self.query_one(PostView).refresh_posts()

    async def action_inject_topic(self, topic: str):
        new_post = await asyncio.to_thread(self.create_post, topic, "USER")
        self.query_one(PostView).add_post(new_post)

    # --- Config File Methods ---

    def get_config_files(self) -> List[str]:
        config_dir = "configs"
        if not os.path.exists(config_dir):
            return []
        return [f for f in os.listdir(config_dir) if f.endswith(".json")]

    async def load_bots_from_json(self, filename: str):
        def _load():
            filepath = os.path.join("configs", filename)
            try:
                with open(filepath, "r") as f:
                    bots_data = json.load(f)
                session.query(Post).delete()
                session.query(Memory).delete()
                session.query(Bot).delete()
                for bot_data in bots_data:
                    memories = bot_data.pop("memories", [])
                    bot = Bot(**bot_data)
                    session.add(bot)
                    for memory_data in memories:
                        memory = Memory(key=memory_data["key"], value=memory_data["value"], bot=bot)
                        session.add(memory)
                session.commit()
                return None
            except (FileNotFoundError, json.JSONDecodeError):
                return "Error"
        
        error = await asyncio.to_thread(_load)
        if error:
            error_post = await asyncio.to_thread(self.create_post, f"Error loading {filename}.", "SYSTEM")
            self.query_one(PostView).add_post(error_post)
        await self.query_one(BotManager).refresh_bots()
        await self.query_one(PostView).refresh_posts()

    async def save_bots_to_json(self, filename: str):
        def _save():
            bots = session.query(Bot).all()
            bots_data = []
            for bot in bots:
                bot_dict = {"name": bot.name, "persona": bot.persona, "model": bot.model}
                memories = [{"key": m.key, "value": m.value} for m in bot.memories]
                if memories:
                    bot_dict["memories"] = memories
                bots_data.append(bot_dict)
            
            filepath = os.path.join("configs", f"{filename}.json")
            with open(filepath, "w") as f:
                json.dump(bots_data, f, indent=4)
        await asyncio.to_thread(_save)

    # --- Database Helper Methods ---

    def db_add_memory(self, memory: Memory):
        session.add(memory)
        session.commit()

    def create_post(self, content, sender, bot=None):
        new_post = Post(content=content, sender=sender, bot=bot)
        session.add(new_post)
        session.commit()
        return new_post
        
    def db_create_bot(self, name, persona, model):
        new_bot = Bot(name=name, persona=persona, model=model)
        session.add(new_bot)
        session.commit()

    def db_edit_bot(self, bot, name, persona, model):
        bot.name = name
        bot.persona = persona
        bot.model = model
        session.commit()

    def db_delete_bot(self, bot):
        session.delete(bot)
        session.commit()

    def db_clear_posts(self):
        session.query(Post).delete()
        session.commit()

    async def action_quit(self) -> None:
        self.log("Stopping bot timer...")
        self.bot_timer.stop()
        
        self.log("Stopping any playing audio...")
        voice_manager.stop_audio()

        self.log(f"Cancelling {len(self.background_tasks)} background tasks...")
        for task in self.background_tasks:
            task.cancel()
        
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        self.log("Closing database connection...")
        await asyncio.to_thread(close_database_connection)
        
        self.log("Exiting application.")
        self.exit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Bot Social Network",
        description="""A fully interactive terminal application that simulates a social media feed for autonomous AI agents. 
Create bots with unique personas, drop them into the chat, and watch as they develop conversations, 
share ideas, and interact with each other in real-time.
""",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
--------------------------------------------------------------------------------
Usage Examples:
  # Run with default settings (loads 'default.json')
  python3 main.py

  # Load a specific group of bots and start the conversation immediately
  python3 main.py --config example_tinydolphin.json --autostart

  # Start a fresh, voiced conversation with the Gemini showcase bots
  python3 main.py --config gemini_models_showcase.json --autostart --tts --clear-db

--------------------------------------------------------------------------------
Requirements:
  - Python 3.9+
  - An API key for the Google Gemini API (set via a .env file).
  - For TTS: A Google Cloud project with the Text-to-Speech API enabled and
    application-default authentication (e.g., run 'gcloud auth application-default login').
  - For local models: Ollama installed and running (https://ollama.com).
"""
    )
    parser.add_argument(
        "--config", 
        type=str, 
        default="default.json", 
        help="The bot configuration file to load from the 'configs/' directory.\n(default: default.json)"
    )
    parser.add_argument(
        "--autostart", 
        action="store_true", 
        help="Start the bot chat automatically on launch."
    )
    parser.add_argument(
        "--clear-db", 
        action="store_true", 
        help="Clear the posts database on launch for a clean slate."
    )
    parser.add_argument(
        "--tts", 
        action="store_true", 
        help="Enable text-to-speech on launch. Requires Google Cloud authentication."
    )
    args = parser.parse_args()

    app = BotSocialApp(
        config_file=args.config,
        autostart=args.autostart, 
        clear_db=args.clear_db, 
        autostart_tts=args.tts
    )
    app.run()

