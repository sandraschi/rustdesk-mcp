"""PyInstaller entry point."""
import _strptime  # noqa: F401
import sys
sys.path.insert(0, "src")
from rustdesk_mcp.server import main
sys.exit(main())

