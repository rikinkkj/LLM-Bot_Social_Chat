
import json
import argparse
import random
import logging
import asyncio
import subprocess
from typing import Optional, List, Tuple

from textual.app import App, ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Header, Footer, ListView, ListItem, Label, Input, Button, Static, TextArea, Select
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.binding import Binding

from database import Bot, Post, session, close_database_connection
import ai_client

# --- Model Loading ---

def get_available_models() -> List[Tuple[str, str]]:
    """Gets a list of available models from Gemini and Ollama."""
    
    # Static list of Gemini models
    gemini_models = [
        ("Gemini 1.5 Flash", "gemini-1.5-flash"),
        ("Gemini 1.5 Pro", "gemini-1.5-pro"),
        ("Gemini 2.5 Flash", "gemini-2.5-flash"),
        ("Gemini 2.5 Pro", "gemini-2.5-pro"),
    ]

    # Dynamically get Ollama models
    ollama_models = []
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            for line in lines[1:]:
                parts = line.split()
                if parts:
                    # Strip the tag (e.g., ':latest') from the model name
                    model_name = parts[0].split(':')[0]
                    ollama_models.append((model_name, model_name))
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        logging.warning(f"Could not list Ollama models: {e}")

    return gemini_models + ollama_models

AVAILABLE_MODELS = get_available_models()

# --- Logging Setup ---
logging.basicConfig(
    level="INFO",
    filename="bots.log",
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Screens ---

class BotEditScreen(ModalScreen[dict]):
    """A modal screen for creating or editing a bot."""

    def __init__(self, bot_to_edit: Optional[Bot] = None, available_models: List[Tuple[str, str]] = []):
        super().__init__()
        self.bot_to_edit = bot_to_edit
        self.available_models = available_models

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="dialog"):
            if self.bot_to_edit:
                yield Label("Edit Bot")
            else:
                yield Label("Create New Bot")
            
            yield Input(
                value=self.bot_to_edit.name if self.bot_to_edit else "",
                placeholder="Name",
                id="bot_name"
            )
            yield TextArea(
                text=self.bot_to_edit.persona if self.bot_to_edit else "",
                id="bot_persona"
            )
            yield Select(
                self.available_models,
                value=self.bot_to_edit.model if self.bot_to_edit else None,
                prompt="Select model",
                id="bot_model"
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

class BotManager(ListView):
    def on_mount(self) -> None:
        self.border_title = "Bots"
        self.app.run_task(self.refresh_bots())

    async def refresh_bots(self):
        def _get_bots():
            return session.query(Bot).all()
        bots = await asyncio.to_thread(_get_bots)
        self.clear()
        for bot in bots:
            self.append(ListItem(Label(bot.name)))

class PostView(ListView):
    def on_mount(self) -> None:
        self.border_title = "Posts"
        self.app.run_task(self.refresh_posts())

    def add_post(self, post: Post):
        sender = post.sender if post.sender else post.bot.name
        self.mount(ListItem(Static(f"{sender}: {post.content}")), before=0)

    async def refresh_posts(self):
        def _get_posts():
            return session.query(Post).order_by(Post.id.desc()).all()
        posts = await asyncio.to_thread(_get_posts)
        self.clear()
        for post in posts:
            sender = post.sender if post.sender else post.bot.name
            self.append(ListItem(Static(f"{sender}: {post.content}")))

class BotSocialApp(App):
    CSS_PATH = "style.css"
    BINDINGS = [Binding("q", "quit", "Quit")]

    def __init__(self):
        super().__init__()
        self.background_tasks = set()
        self.selected_bot: Optional[Bot] = None
        self.available_models = get_available_models()
        logging.info("Application started.")

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Vertical(
                BotManager(),
                Horizontal(
                    Button("Create Bot", id="create_bot"),
                    Button("Edit Bot", id="edit_bot"),
                ),
                Button("Delete Bot", id="delete_bot"),
                Horizontal(
                    Button("Load Bots", id="load_bots"),
                    Button("Save Bots", id="save_bots"),
                ),
                id="left-pane"
            ),
            Vertical(
                PostView(),
                Horizontal(
                    Button("Start", id="start_chat"),
                    Button("Stop", id="stop_chat"),
                    Button("Clear", id="clear_chat"),
                ),
                Horizontal(
                    Input(placeholder="Topic", id="topic_input"),
                    Button("Inject Topic", id="inject_topic"),
                ),
                id="right-pane"
            )
        )
        yield Footer()

    def on_mount(self) -> None:
        self.bot_timer = self.set_interval(8, self.run_bot_activity, pause=True)

    def on_list_view_selected(self, event: ListView.Selected):
        if isinstance(event.list_view, BotManager):
            bot_name = event.item.children[0].renderable
            self.run_task(self.select_bot_by_name(bot_name))
    
    async def select_bot_by_name(self, name: str):
        def _get_bot():
            return session.query(Bot).filter_by(name=name).first()
        self.selected_bot = await asyncio.to_thread(_get_bot)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "topic_input" and event.value:
            await self.action_inject_topic(event.value)
            event.input.value = ""

    def run_task(self, coro):
        task = asyncio.create_task(coro)
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

    async def run_bot_activity(self):
        bots = await asyncio.to_thread(session.query(Bot).all)
        if not bots:
            return

        bot_to_post = random.choice(bots)
        recent_posts = await asyncio.to_thread(
            session.query(Post).order_by(Post.id.desc()).limit(5).all
        )

        post_content = ""
        try:
            if bot_to_post.model.startswith("gemini"):
                post_content = await ai_client.generate_post_gemini(bot_to_post, recent_posts)
            else:
                post_content = await ai_client.generate_post_ollama(bot_to_post, recent_posts)
        except Exception as e:
            post_content = f"[SYSTEM Error: {e}]"

        sender_name = "SYSTEM" if post_content.startswith(("[Error", "[SYSTEM")) else bot_to_post.name
        new_post = await asyncio.to_thread(self.create_post, post_content, sender_name, bot_to_post)
        self.query_one(PostView).add_post(new_post)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create_bot":
            self.push_screen(BotEditScreen(available_models=self.available_models), self.handle_bot_edit_result)
        elif event.button.id == "edit_bot":
            if self.selected_bot:
                self.push_screen(BotEditScreen(bot_to_edit=self.selected_bot, available_models=self.available_models), self.handle_bot_edit_result)
        elif event.button.id == "delete_bot":
            if self.selected_bot:
                self.run_task(self.action_delete_bot())
        elif event.button.id == "load_bots":
            self.run_task(self.load_bots_from_json())
        elif event.button.id == "save_bots":
            self.run_task(self.save_bots_to_json())
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

    def handle_bot_edit_result(self, bot_data: Optional[dict]):
        if bot_data:
            if self.selected_bot: # It's an edit
                self.run_task(self.action_edit_bot(bot_data))
            else: # It's a create
                self.run_task(self.action_create_bot(bot_data))

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

    # --- Database Helper Methods ---
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

    async def load_bots_from_json(self):
        def _load():
            try:
                with open("bots.json", "r") as f:
                    bots_data = json.load(f)
                session.query(Bot).delete()
                for bot_data in bots_data:
                    bot = Bot(name=bot_data["name"], persona=bot_data["persona"], model=bot_data.get("model", "gemini-1.5-flash"))
                    session.add(bot)
                session.commit()
                return None
            except FileNotFoundError:
                return "FileNotFound"
            except json.JSONDecodeError:
                return "JSONDecodeError"
        
        error = await asyncio.to_thread(_load)
        if error == "JSONDecodeError":
            error_post = await asyncio.to_thread(self.create_post, "Error: bots.json is malformed or corrupted.", "SYSTEM")
            self.query_one(PostView).add_post(error_post)
        await self.query_one(BotManager).refresh_bots()

    async def save_bots_to_json(self):
        def _save():
            bots = session.query(Bot).all()
            bots_data = [{"name": bot.name, "persona": bot.persona, "model": bot.model} for bot in bots]
            with open("bots.json", "w") as f:
                json.dump(bots_data, f, indent=4)
        await asyncio.to_thread(_save)

    async def action_quit(self) -> None:
        self.log("Stopping bot timer...")
        self.bot_timer.stop()
        
        self.log(f"Cancelling {len(self.background_tasks)} background tasks...")
        for task in self.background_tasks:
            task.cancel()
        
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        self.log("Closing database connection...")
        await asyncio.to_thread(close_database_connection)
        
        self.log("Exiting application.")
        self.exit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A TUI-based social network for AI bots.")
    parser.add_argument("--llm", type=str, default="gemini", choices=["gemini", "ollama"],
                        help="DEPRECATED: This argument is no longer used.")
    args = parser.parse_args()

    app = BotSocialApp()
    app.run()
