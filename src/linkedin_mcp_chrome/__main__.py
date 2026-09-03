"""Entry point — hand off to upstream mcp-server-linkedin.

This wrapper adds no runtime behavior. Its whole purpose is the
`fastmcp>=3.4.4,<4.0` pin declared in `pyproject.toml`, which prevents
`uvx` from resolving `fastmcp==4.0.0` and crashing at import (see docs/how-it-works.md).

Everything else — the LinkedIn browser profile, the Patchright Chromium
download, all 17 tools — comes from `mcp-server-linkedin` unchanged.
"""
from __future__ import annotations

import sys

from . import __version__


def main() -> int:
    """Print a version banner, then hand off to upstream's CLI main."""
    print(
        f"[linkedin-mcp-chrome v{__version__}] Wrapping mcp-server-linkedin "
        f"with fastmcp<4 pin",
        file=sys.stderr,
    )
    from linkedin_mcp_server.cli_main import main as upstream_main
    return upstream_main()


if __name__ == "__main__":
    sys.exit(main())
