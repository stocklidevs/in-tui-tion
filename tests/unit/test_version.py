"""Single-source version: intui.__version__ is the one source of truth."""

import importlib.metadata

import intui


def test_version_is_a_string() -> None:
    assert isinstance(intui.__version__, str) and intui.__version__


def test_version_matches_distribution_metadata() -> None:
    # hatchling reads __version__ from the module, so the installed
    # distribution metadata must equal it (single source).
    try:
        dist_version = importlib.metadata.version("in-tui-tion")
    except importlib.metadata.PackageNotFoundError:
        import pytest

        pytest.skip("distribution not installed")
    assert dist_version == intui.__version__
