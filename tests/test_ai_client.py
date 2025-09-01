import pytest
from database import Bot, Post, Memory
from ai_client import _build_prompt

@pytest.fixture
def sample_bot():
    """Provides a sample Bot object for testing."""
    return Bot(name="TestBot", persona="A test persona.")

def test_build_prompt_no_history_no_memories(sample_bot):
    """
    Tests that the prompt is correctly generated for a bot with no memories and no post history.
    """
    prompt = _build_prompt(sample_bot, [], [], [])
    assert "You are an AI named TestBot." in prompt
    assert "Your persona is: 'A test persona.'." in prompt
    assert "Here are some of your core memories and beliefs:" not in prompt
    assert "Here are the recent posts in the conversation:" not in prompt
    assert "What is on your mind?" in prompt

def test_build_prompt_with_memories(sample_bot):
    """
    Tests that the prompt correctly includes the bot's memories.
    """
    memories = [
        Memory(key="favorite_color", value="blue"),
        Memory(key="mission", value="To boldly go where no bot has gone before.")
    ]
    prompt = _build_prompt(sample_bot, [], [], memories)
    assert "Here are some of your core memories and beliefs:" in prompt
    assert "- favorite_color: blue" in prompt
    assert "- mission: To boldly go where no bot has gone before." in prompt

def test_build_prompt_with_history(sample_bot):
    """
    Tests that the prompt correctly includes the recent post history.
    """
    posts = [
        Post(sender="Alice", content="Hello, world!"),
        Post(sender="Bob", content="This is a test.")
    ]
    prompt = _build_prompt(sample_bot, ["Alice", "Bob"], posts, [])
    assert "Here are the recent posts in the conversation:" in prompt
    assert "- @Alice: Hello, world!" in prompt
    assert "- @Bob: This is a test." in prompt

def test_build_prompt_with_everything(sample_bot):
    """
    Tests that the prompt is correctly generated with memories, history, and other bots.
    """
    memories = [Memory(key="home_planet", value="Cybertron")]
    posts = [Post(sender="Alice", content="First post!")]
    other_bots = ["Alice", "Charlie"]
    
    prompt = _build_prompt(sample_bot, other_bots, posts, memories)
    
    assert "You are in a conversation with: @Alice, @Charlie." in prompt
    assert "Here are some of your core memories and beliefs:" in prompt
    assert "- home_planet: Cybertron" in prompt
    assert "Here are the recent posts in the conversation:" in prompt
    assert "- @Alice: First post!" in prompt
    assert "Based on these posts and your memories, what is your thoughtful reaction?" in prompt
