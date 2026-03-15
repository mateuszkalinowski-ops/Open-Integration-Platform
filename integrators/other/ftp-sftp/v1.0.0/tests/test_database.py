"""Tests for StateStore (polling state persistence)."""

import os

import pytest
import pytest_asyncio
from src.models.database import StateStore


@pytest_asyncio.fixture
async def state_store(tmp_path):
    db_path = str(tmp_path / "test_state.db")
    store = StateStore()
    store._db_path = db_path
    await store.initialize()
    yield store
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.mark.asyncio
async def test_initialize_creates_table(state_store: StateStore):
    await state_store.load_all_timestamps()


@pytest.mark.asyncio
async def test_get_known_files_empty(state_store: StateStore):
    files = await state_store.get_known_files("nonexistent")
    assert files == set()


@pytest.mark.asyncio
async def test_update_and_get_known_files(state_store: StateStore):
    paths = {"/data/a.csv", "/data/b.csv", "/data/c.csv"}
    await state_store.update_known_files("test-account", paths)

    result = await state_store.get_known_files("test-account")
    assert result == paths


@pytest.mark.asyncio
async def test_update_replaces_previous(state_store: StateStore):
    await state_store.update_known_files("acc", {"/old.txt"})
    await state_store.update_known_files("acc", {"/new.txt"})

    result = await state_store.get_known_files("acc")
    assert result == {"/new.txt"}


@pytest.mark.asyncio
async def test_multiple_accounts_isolated(state_store: StateStore):
    await state_store.update_known_files("acc1", {"/a.txt"})
    await state_store.update_known_files("acc2", {"/b.txt"})

    assert await state_store.get_known_files("acc1") == {"/a.txt"}
    assert await state_store.get_known_files("acc2") == {"/b.txt"}
