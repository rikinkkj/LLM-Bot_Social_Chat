
import json
import argparse
import random
import logging
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Label, Input, Button, Static, TextArea
from textual.containers import Horizontal, Vertical
from textual.binding import Binding
from database import Bot, Post, session
import ai_client

# --- Logging Setup ---
logging.basicConfig(
    level="INFO",
    filename="bots.log",
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class BotManager(ListView):
    def on_mount(self) -> None:
        self.border_title = "Bots"
        self.refresh_bots()

    def refresh_bots(self):
        self.clear()
        bots = session.query(Bot).all()
        for bot in bots:
            self.append(ListItem(Label(bot.name)))

class PostView(ListView):
    def on_mount(self) -> None:
        self.border_title = "Posts"
        self.refresh_posts()

    def add_post(self, post: Post):
        sender = post.sender if post.sender else post.bot.name
        self.mount(ListItem(Static(f"{sender}: {post.content}")), before=0)

    def refresh_posts(self):
        self.clear()
        posts = session.query(Post).order_by(Post.id.desc()).all()
        for post in posts:
            sender = post.sender if post.sender else post.bot.name
            self.append(ListItem(Static(f"{sender}: {post.content}")))

class BotSocialApp(App):
    CSS_PATH = "style.css"
    BINDINGS = [Binding("q", "quit", "Quit")]

    def __init__(self, llm_provider="gemini"):
        super().__init__()
        self.llm_provider = llm_provider
        logging.info(f"Application started with LLM provider: {self.llm_provider}")


    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Vertical(
                BotManager(),
                Input(placeholder="Bot name", id="bot_name"),
                TextArea(id="bot_persona", classes="persona-input"),
                Input(placeholder="Model (e.g., gemini-1.5-flash or llama3.2)", id="bot_model"),
                Button("Create Bot", id="create_bot"),
                Horizontal(
                    Button("Edit Bot", id="edit_bot"),
                    Button("Delete Bot", id="delete_bot"),
                ),
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
        self.selected_bot = None
        self.bot_timer = self.set_interval(8, self.run_bot_activity)
        self.bot_timer.pause()

    def on_list_view_selected(self, event: ListView.Selected):
        if isinstance(event.list_view, BotManager):
            bot_name = event.item.children[0].renderable
            self.selected_bot = session.query(Bot).filter_by(name=bot_name).first()
            if self.selected_bot:
                self.query_one("#bot_name", Input).value = self.selected_bot.name
                self.query_one("#bot_persona", TextArea).load_text(self.selected_bot.persona)
                self.query_one("#bot_model", Input).value = self.selected_bot.model

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "topic_input":
            topic = event.value
            if topic:
                new_post = Post(content=f"Let's talk about: {topic}", sender="USER")
                session.add(new_post)
                session.commit()
                self.query_one(PostView).add_post(new_post)
                event.input.value = ""

    async def run_bot_activity(self):
        bots = session.query(Bot).all()
        if not bots:
            return

        bot_to_post = random.choice(bots)
        recent_posts = session.query(Post).order_by(Post.id.desc()).limit(5).all()

        post_content = ""
        try:
            if self.llm_provider == "gemini":
                post_content = await ai_client.generate_post_gemini(bot_to_post, recent_posts)
            elif self.llm_provider == "ollama":
                post_content = await ai_client.generate_post_ollama(bot_to_post, recent_posts)
        except Exception as e:
            # Catch exceptions from the AI client (e.g., API key error)
            post_content = f"[SYSTEM Error: {e}]"

        # If the AI returns an error message, post it as the system
        sender_name = "SYSTEM" if post_content.startswith("[Error") else bot_to_post.name
        
        new_post = Post(content=post_content, bot=bot_to_post, sender=sender_name)
        session.add(new_post)
        session.commit()
        self.query_one(PostView).add_post(new_post)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handles button press events."""
        if event.button.id == "create_bot":
            asyncio.create_task(self.action_create_bot())
        elif event.button.id == "edit_bot":
            asyncio.create_task(self.action_edit_bot())
        elif event.button.id == "delete_bot":
            asyncio.create_task(self.action_delete_bot())
        elif event.button.id == "load_bots":
            asyncio.create_task(self.load_bots_from_json())
        elif event.button.id == "save_bots":
            asyncio.create_task(self.save_bots_to_json())
        elif event.button.id == "start_chat":
            self.bot_timer.resume()
        elif event.button.id == "stop_chat":
            self.bot_timer.pause()
        elif event.button.id == "clear_chat":
            asyncio.create_task(self.action_clear_posts())
        elif event.button.id == "inject_topic":
            asyncio.create_task(self.action_inject_topic())

    async def action_create_bot(self):
        bot_name_input = self.query_one("#bot_name", Input)
        bot_persona_input = self.query_one("#bot_persona", TextArea)
        bot_model_input = self.query_one("#bot_model", Input)
        if bot_name_input.value and bot_persona_input.text and bot_model_input.value:
            await asyncio.to_thread(
                self.db_create_bot,
                bot_name_input.value,
                bot_persona_input.text,
                bot_model_input.value
            )
            self.query_one(BotManager).refresh_bots()
            bot_name_input.value = ""
            bot_persona_input.load_text("")
            bot_model_input.value = ""

    async def action_edit_bot(self):
        bot_name_input = self.query_one("#bot_name", Input)
        bot_persona_input = self.query_one("#bot_persona", TextArea)
        bot_model_input = self.query_one("#bot_model", Input)
        if self.selected_bot and bot_name_input.value and bot_persona_input.text and bot_model_input.value:
            await asyncio.to_thread(
                self.db_edit_bot,
                self.selected_bot,
                bot_name_input.value,
                bot_persona_input.text,
                bot_model_input.value
            )
            self.query_one(BotManager).refresh_bots()

    async def action_delete_bot(self):
        bot_name_input = self.query_one("#bot_name", Input)
        bot_persona_input = self.query_one("#bot_persona", TextArea)
        bot_model_input = self.query_one("#bot_model", Input)
        if self.selected_bot:
            await asyncio.to_thread(self.db_delete_bot, self.selected_bot)
            self.selected_bot = None
            bot_name_input.value = ""
            bot_persona_input.load_text("")
            bot_model_input.value = ""
            self.query_one(BotManager).refresh_bots()

    async def action_clear_posts(self):
        await asyncio.to_thread(self.db_clear_posts)
        self.query_one(PostView).refresh_posts()

    async def action_inject_topic(self):
        topic_input = self.query_one("#topic_input", Input)
        if topic_input.value:
            new_post = await asyncio.to_thread(self.create_post, topic_input.value, "USER")
            self.query_one(PostView).add_post(new_post)
            topic_input.value = ""

    # --- Database Helper Methods ---
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
        self.query_one(BotManager).refresh_bots()

    async def save_bots_to_json(self):
        def _save():
            bots = session.query(Bot).all()
            bots_data = [{"name": bot.name, "persona": bot.persona, "model": bot.model} for bot in bots]
            with open("bots.json", "w") as f:
                json.dump(bots_data, f, indent=4)
        await asyncio.to_thread(_save)

    def action_quit(self) -> None:
        """Gracefully shut down the application."""
        self.bot_timer.stop()
        self.log("Bot timer stopped. Exiting application.")
        self.exit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A TUI-based social network for AI bots.")
    parser.add_argument("--llm", type=str, default="gemini", choices=["gemini", "ollama"],
                        help="The language model provider to use.")
    args = parser.parse_args()

    app = BotSocialApp(llm_provider=args.llm)
    app.run()
