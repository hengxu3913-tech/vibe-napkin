"""Tests for the zvec bridge module."""

from vibe_napkin.core.zvec_bridge import check_zvec_available


def test_zvec_not_available():
    """If zvec is not installed, check returns False."""
    assert check_zvec_available() is False