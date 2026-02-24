"""Shared test fixtures for Slack integrator tests."""

import os

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("SLACK_POLLING_ENABLED", "false")
os.environ.setdefault("KAFKA_ENABLED", "false")


@pytest.fixture
def slack_api_response_ok() -> dict:
    """Standard successful Slack API response."""
    return {"ok": True}


@pytest.fixture
def slack_auth_test_response() -> dict:
    return {
        "ok": True,
        "url": "https://test-workspace.slack.com/",
        "team": "Test Workspace",
        "user": "testbot",
        "team_id": "T12345",
        "user_id": "U12345",
        "bot_id": "B12345",
    }


@pytest.fixture
def slack_conversations_list_response() -> dict:
    return {
        "ok": True,
        "channels": [
            {
                "id": "C001",
                "name": "general",
                "is_channel": True,
                "is_private": False,
                "is_im": False,
                "is_mpim": False,
                "is_archived": False,
                "is_member": True,
                "num_members": 42,
                "topic": {"value": "Company-wide announcements"},
                "purpose": {"value": "General discussion"},
            },
            {
                "id": "C002",
                "name": "random",
                "is_channel": True,
                "is_private": False,
                "is_im": False,
                "is_mpim": False,
                "is_archived": False,
                "is_member": True,
                "num_members": 38,
                "topic": {"value": ""},
                "purpose": {"value": "Random stuff"},
            },
        ],
        "response_metadata": {"next_cursor": ""},
    }


@pytest.fixture
def slack_conversations_history_response() -> dict:
    return {
        "ok": True,
        "messages": [
            {
                "type": "message",
                "user": "U12345",
                "text": "Hello, world!",
                "ts": "1677000001.000001",
                "thread_ts": "",
            },
            {
                "type": "message",
                "user": "U67890",
                "text": "Hi there!",
                "ts": "1677000002.000002",
                "thread_ts": "",
            },
        ],
        "has_more": False,
    }


@pytest.fixture
def slack_chat_post_message_response() -> dict:
    return {
        "ok": True,
        "channel": "C001",
        "ts": "1677000003.000003",
        "message": {
            "text": "Test message",
            "user": "U12345",
            "ts": "1677000003.000003",
        },
    }


@pytest.fixture
def slack_users_info_response() -> dict:
    return {
        "ok": True,
        "user": {
            "id": "U12345",
            "name": "testuser",
            "real_name": "Test User",
        },
    }
