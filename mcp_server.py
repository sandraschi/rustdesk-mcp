#!/usr/bin/env python3
"""
Standalone MCP server entry point for Cursor.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

try:
    # Import and run the server
    from rustdesk_mcp.server import main

    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    print("Make sure the rustdesk-mcp package is installed or src is in PYTHONPATH", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Server startup error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)