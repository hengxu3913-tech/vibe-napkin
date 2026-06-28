"""Tests for the checkpoint model."""

from vibe_napkin.models.checkpoint import (
    Checkpoint,
    save_checkpoint,
    load_checkpoint,
    list_checkpoints,
    get_next_checkpoint,
)


def test_save_and_load_checkpoint(tmp_project):
    """Save then load a checkpoint returns the same data."""
    cp = Checkpoint(
        checkpoint_id="2026-06-29-001-test",
        label="test-label",
        git_commit="abc123",
        business_units=["001-test.md"],
        todo="Next: implement feature",
    )
    save_checkpoint(tmp_project, cp)

    loaded = load_checkpoint(tmp_project, "2026-06-29-001-test")
    assert loaded is not None
    assert loaded.checkpoint_id == cp.checkpoint_id
    assert loaded.label == cp.label
    assert loaded.todo == cp.todo


def test_load_nonexistent_returns_none(tmp_project):
    """Loading a non-existent checkpoint returns None."""
    cp = load_checkpoint(tmp_project, "nonexistent")
    assert cp is None


def test_list_checkpoints(tmp_project):
    """list_checkpoints returns all saved checkpoints sorted."""
    cp1 = Checkpoint(checkpoint_id="2026-06-28-001-first", label="first")
    cp2 = Checkpoint(checkpoint_id="2026-06-29-001-second", label="second")
    save_checkpoint(tmp_project, cp1)
    save_checkpoint(tmp_project, cp2)

    checkpoints = list_checkpoints(tmp_project)
    assert len(checkpoints) == 2
    assert checkpoints[0].checkpoint_id == "2026-06-28-001-first"
    assert checkpoints[1].checkpoint_id == "2026-06-29-001-second"


def test_get_next_checkpoint_generates_id(tmp_project):
    """get_next_checkpoint generates a valid ID."""
    cp = get_next_checkpoint(tmp_project, "测试标签")
    assert cp.label == "测试标签"
    assert cp.checkpoint_id
    assert "测试" in cp.checkpoint_id


def test_get_next_checkpoint_increments_serial(tmp_project):
    """Sequential calls increment the serial number."""
    cp1 = get_next_checkpoint(tmp_project, "first")
    save_checkpoint(tmp_project, cp1)

    cp2 = get_next_checkpoint(tmp_project, "second")
    save_checkpoint(tmp_project, cp2)

    assert cp1.checkpoint_id != cp2.checkpoint_id


def test_empty_list(tmp_project):
    """list_checkpoints returns empty list when no checkpoints exist."""
    assert list_checkpoints(tmp_project) == []