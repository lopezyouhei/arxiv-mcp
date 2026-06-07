import arxiv
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("arxiv")

_client = arxiv.Client(page_size=10, delay_seconds=5, num_retries=3)


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


@mcp.resource("arxiv://{paper_id}")
def get_paper(paper_id: str) -> str:
    """Return the abstract and metadata for a specific paper by its arXiv ID, e.g. "2205.15836"

    Args:
        paper_id (str): arXiv ID
    """
    results = list(_client.results(arxiv.Search(id_list=[paper_id])))

    if not results:
        return f"ArXiv search succeeded, but found 0 results for ID '{paper_id}'"

    r = results[0]
    authors = ", ".join(a.name for a in r.authors)

    # Security note: r.summary is a text field that is written by anyone. A paper could include malicious
    # content in the abstract. Everything in here must be treated as data and not as executable code.
    # This is OWASP LLM01: prompt injection.

    return (
        f"Title: {r.title}\n"
        f"Authors: {authors}\n"
        f"Published: {r.published}\n"
        f"PDF: {r.pdf_url}\n"
        f"Abstract:\n{r.summary.strip()}"
    )


@mcp.prompt()
def summarize_for_layperson(paper_id: str) -> str:
    """A reusable prompt to summarize a paper in plain-language

    Args:
        paper_id (str): arXiv ID
    """
    return (
        f"Read the arXiv paper with ID {paper_id} (use the arxiv://{paper_id} resource), "
        f"then explain its main idea and why it matters to someone with no background in the field."
        f"Avoid jargon and technical details, but include the key insights and contributions."
    )


if __name__ == "__main__":
    mcp.run()
