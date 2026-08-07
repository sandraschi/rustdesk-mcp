#!/usr/bin/env python3
"""
Main entry point for the rustdesk_mcp package.

This allows the package to be executed with: python -m rustdesk_mcp
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    # Import and run the MCP server
    from rustdesk_mcp.mcp_server import main

    if __name__ == "__main__":
        asyncio.run(main())

except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    print("Make sure the rustdesk-mcp package is installed or src is in PYTHONPATH", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Server startup error: {e}", file=sys.stderr)
    import traceback

    traceback.print_exc()
    sys.exit(1)
