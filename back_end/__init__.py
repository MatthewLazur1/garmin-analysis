import os

from dotenv import load_dotenv

# Load .env relative to this file's location, not the process's cwd — external
# launchers (MCP clients, Claude Desktop, etc.) invoke this package without
# first cd-ing into the project directory, and load_dotenv() searches from cwd
# by default.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))
