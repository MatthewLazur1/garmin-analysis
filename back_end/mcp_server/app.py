from mcp.server.fastmcp import FastMCP

# Single shared FastMCP instance. Lives in its own module (rather than in server.py)
# so it's never re-created as a duplicate when server.py is run as `__main__`.
mcp = FastMCP("garmin-performance")
