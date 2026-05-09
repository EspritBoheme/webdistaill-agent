"""CLI entry point for WebDistill."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from router import Router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="webdistill",
        description="WebDistill — AI Web Intelligence & Distillation Framework",
    )
    parser.add_argument(
        "url",
        help="Public URL to distill",
    )
    parser.add_argument(
        "--mode",
        choices=["default", "technical", "raw", "full"],
        default="default",
        help="Processing mode (default: default)",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        dest="output_format",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    router = Router()
    task = router.create_task(
        url=args.url,
        mode=args.mode,
        output_format=args.output_format,
    )

    result = router.execute(task)

    if not result.ok:
        logger.error("Task failed: %s", result.error)
        return 1

    output = result.formatted_output.content

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
        logger.info("Output written to %s", args.output)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
