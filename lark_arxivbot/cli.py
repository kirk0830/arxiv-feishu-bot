"""Command-line interface for lark-arxivbot."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import List, Optional

from lark_arxivbot.availability import run_availability_checks
from lark_arxivbot.config import (
    DEFAULT_DAYS_BACK,
    DEFAULT_MAX_PAPERS,
    DEFAULT_MAX_RESULTS,
)
from lark_arxivbot.logging_config import setup_logging
from lark_arxivbot.workflow import run_daily_workflow

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI.

    Returns
    -------
    argparse.ArgumentParser
        Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="lark-arxivbot",
        description="Daily arXiv paper digest bot for Feishu (Lark).",
    )
    parser.add_argument(
        "--category",
        action="append",
        default=None,
        help="arXiv category (repeatable). Defaults to config.",
    )
    parser.add_argument(
        "--keyword",
        action="append",
        default=None,
        help="Search keyword (repeatable). Defaults to config.",
    )
    parser.add_argument(
        "--channel",
        choices=["api", "atom", "all"],
        default="all",
        help="Retrieval channel. Defaults to 'all'.",
    )
    parser.add_argument(
        "--check-availability",
        action="store_true",
        default=False,
        help="Run pre-flight availability checks.",
    )
    parser.add_argument(
        "--exit-on-failed-check",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Exit immediately if any availability check fails.",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=DEFAULT_MAX_RESULTS,
        help="Maximum results to request from arXiv.",
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=DEFAULT_DAYS_BACK,
        help="Number of days back to search.",
    )
    parser.add_argument(
        "--max-papers",
        type=int,
        default=DEFAULT_MAX_PAPERS,
        help="Maximum papers to push.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> None:
    """CLI entry point for lark-arxivbot.

    Parameters
    ----------
    argv : Optional[List[str]], optional
        Command-line arguments. Defaults to ``sys.argv[1:]``.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    setup_logging()

    if args.check_availability:
        results = run_availability_checks(args.channel)
        failed = [k for k, v in results.items() if not v]
        if failed:
            msg = (
                f"Availability checks failed for: {', '.join(failed)}"
            )
            if args.exit_on_failed_check:
                logger.critical(msg)
                sys.exit(1)
            logger.warning(msg)

    run_daily_workflow(
        categories=args.category,
        keywords=args.keyword,
        channel=args.channel,
        max_results=args.max_results,
        days_back=args.days_back,
        max_papers=args.max_papers,
    )


if __name__ == "__main__":
    main()
