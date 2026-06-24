"""Tests for lark_arxivbot.cli module."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from lark_arxivbot.cli import main
from lark_arxivbot.config import (
    DEFAULT_DAYS_BACK,
    DEFAULT_MAX_PAPERS,
    DEFAULT_MAX_RESULTS,
)


_DEFAULT_CATEGORY_EXPR = (
    '"physics.chem-ph"||"cond-mat.mtrl-sci"||"physics.comp-ph"'
)
_DEFAULT_KEYWORD_EXPR = (
    '"molecular dynamics"&&'
    '("machine learning"||"deep learning"||"neural network")'
)


@patch("lark_arxivbot.cli.setup_logging")
@patch("lark_arxivbot.cli.run_daily_workflow")
def test_cli_defaults(
    mock_workflow: MagicMock,
    mock_setup: MagicMock,
) -> None:
    """Assert CLI with no args calls workflow with defaults."""
    main([])

    mock_workflow.assert_called_once_with(
        categories=_DEFAULT_CATEGORY_EXPR,
        keywords=_DEFAULT_KEYWORD_EXPR,
        channel="all",
        max_results=DEFAULT_MAX_RESULTS,
        days_back=DEFAULT_DAYS_BACK,
        max_papers=DEFAULT_MAX_PAPERS,
    )


@patch("lark_arxivbot.cli.setup_logging")
@patch("lark_arxivbot.cli.run_availability_checks")
@patch("lark_arxivbot.cli.run_daily_workflow")
@patch("lark_arxivbot.cli.sys.exit")
def test_cli_check_availability_exits_on_failure(
    mock_exit: MagicMock,
    mock_workflow: MagicMock,
    mock_checks: MagicMock,
    mock_setup: MagicMock,
) -> None:
    """Assert --check-availability exits when a check fails."""
    mock_checks.return_value = {
        "network": False,
        "arxiv": True,
        "llm": True,
    }
    mock_exit.side_effect = SystemExit(1)

    with pytest.raises(SystemExit):
        main(["--check-availability"])

    mock_exit.assert_called_once_with(1)
    mock_workflow.assert_not_called()


@patch("lark_arxivbot.cli.setup_logging")
@patch("lark_arxivbot.cli.run_availability_checks")
@patch("lark_arxivbot.cli.run_daily_workflow")
@patch("lark_arxivbot.cli.sys.exit")
def test_cli_check_availability_continues_when_no_exit(
    mock_exit: MagicMock,
    mock_workflow: MagicMock,
    mock_checks: MagicMock,
    mock_setup: MagicMock,
) -> None:
    """Assert --no-exit-on-failed-check allows workflow to continue."""
    mock_checks.return_value = {
        "network": False,
        "arxiv": True,
        "llm": True,
    }

    main(["--check-availability", "--no-exit-on-failed-check"])

    mock_exit.assert_not_called()
    mock_workflow.assert_called_once()


@patch("lark_arxivbot.cli.setup_logging")
@patch("lark_arxivbot.cli.run_daily_workflow")
def test_cli_passes_args_to_run_daily_workflow(
    mock_workflow: MagicMock,
    mock_setup: MagicMock,
) -> None:
    """Assert CLI arguments are forwarded to workflow."""
    main([
        "--category", '"physics.bio-ph"||"cond-mat.stat-mech"',
        "--keyword", '"force field"&&"coarse-grained"',
        "--channel", "api",
        "--max-results", "20",
        "--days-back", "3",
        "--max-papers", "5",
    ])

    mock_workflow.assert_called_once_with(
        categories='"physics.bio-ph"||"cond-mat.stat-mech"',
        keywords='"force field"&&"coarse-grained"',
        channel="api",
        max_results=20,
        days_back=3,
        max_papers=5,
    )
