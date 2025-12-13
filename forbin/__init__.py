"""Forbin - Interactive CLI tool for testing remote MCP servers."""

import asyncio
import sys
from forbin.forbin import main


def cli():
    """CLI entry point that wraps the async main function."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)


__all__ = ["main", "cli"]
