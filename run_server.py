"""PyInstaller entry point."""
import _strptime  # noqa: F401
import mcp.types  # noqa: F401  (freeze the mcp bootstrap before fastmcp imports it)
import os
import sys

# console=False in the spec leaves sys.stderr=None under PyInstaller; uvicorn's
# logging then crashes on startup. Give it a real sink so logs don't blow up.
if getattr(sys, "stderr", None) is None:
    sys.stderr = open(os.devnull, "w")

sys.path.insert(0, "src")
from rustdesk_mcp.server import main

sys.exit(main())

