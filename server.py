from mcp.server.fastmcp import FastMCP

mcp = FastMCP("arxiv")


@mcp.tool()
def ping() -> str:
    """Health check. Returns a fixed string to confirm the server is running."""
    return "arxiv server is alive"


if __name__ == "__main__":
    mcp.run()
