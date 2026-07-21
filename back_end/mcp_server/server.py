from back_end.mcp_server.app import mcp
from back_end.mcp_server import plan_tools, garmin_tools, rag_tools  # noqa: F401 - registers tools on `mcp`


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
