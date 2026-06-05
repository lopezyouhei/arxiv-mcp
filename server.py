import arxiv
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("arxiv")

_client = arxiv.Client(page_size=10, delay_seconds=3, num_retries=3)


@mcp.tool()
def search_papers(query: str, max_results: int = 5) -> str:
    """Search arXiv for papers matching a query

    Args:
        query (str): words or phrases to search for, e.g. "vision transformer", "deep learning for NLP", "graph neural networks"
        max_results (int, optional): how many papers to return. Defaults to 5.
    """
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    try:
        results = list(_client.results(search))
    except Exception as e:
        msg = str(e)
        if "429" in msg or "rate" in msg.lower():
            return "arXiv is rate limiting requests (HTTP 429). Wait ~10-15 seconds and try again."
        return f"Search failed: {msg}"

    if not results:
        return f"No papers found for query: {query}"

    lines = []
    for r in results:
        paper_id = r.entry_id.split("/abs/")[-1]
        lines.append(f"- {r.title} (id: {paper_id})\n{r.summary[:200].strip()}...")

    return "\n".join(lines)


@mcp.tool()
def ping() -> str:
    """A simple tool to check if the server is responsive."""
    return "pong"


if __name__ == "__main__":
    mcp.run()
