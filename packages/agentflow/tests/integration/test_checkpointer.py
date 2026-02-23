from __future__ import annotations

from pathlib import Path

import pytest
from agentflow.workflow.checkpointer import create_checkpointer


@pytest.mark.integration
@pytest.mark.asyncio
async def test_creates_working_checkpointer(tmp_path: Path) -> None:
    db_path = str(tmp_path / "checkpoints.db")
    saver = await create_checkpointer(db_path)

    assert saver.conn is not None
    assert Path(db_path).exists()

    await saver.conn.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_connection_closes_cleanly(tmp_path: Path) -> None:
    db_path = str(tmp_path / "checkpoints.db")
    saver = await create_checkpointer(db_path)

    await saver.conn.close()
