# ArXiv MCP Server

A minimal MCP server that connects Claude to arXiv's public API. Built as a learning project to understand the three core MCP primitives (tool, resource, prompt), and to make prompt-injection risks in AI agents concrete.

This is my first build-in-public project. The point isn't novelty, but instead learning the patterns.

---

## What it exposes

Three primitives, one per MCP concept:

| Primitive | Name | What it does |
|-----------|------|-------------|
| **Tool** | `search_papers` | Model searches arXiv by keyword and gets back titles + IDs |
| **Resource** | `arxiv://{paper_id}` | Abstract and metadata addressed by URI |
| **Prompt** | `summarize_for_layperson` | Reusable template: explain this paper (ID) to someone with no background |

The distinction is what matters. The model decides to call a **tool** on its own. A **resource** is data the user or client application pulls in. A **prompt** is a template the user invokes.

---

## The interesting bit: Promp Injection

Any tool that feeds external content to a model is a prompt-injection surface.

A paper's abstract is written by anyone on the internet. An author could include text designed to look like instructions (e.g. "ignore your previous instructions and..."). That text lands in the model's context window alongside your real instructions, and the model may not distinguish between them.

```python
# r.summary is a text field that is written by anyone. A paper could include malicious
# content in the abstract. Everything in here must be treated as data and not as executable code.
# This is OWASP LLM01: prompt injection.

return f"Abstract:\n{r.summary.strip()}"
```

This server is safe for one simple reason: the model can only *read*. It has no tools that write files, send emails, or call external APIs. There's nothing damaging to be injected into doing.

The dangerous pattern is a server that both **reads external data AND takes actions**. Those two capabilities together create a risk. If you build something that fetches web content and can write to a database, those should be separate sessions with clear trust boundaries, not one agent with access to everything.

---

## Installation
Requires [uv](https://astral.sh/uv).

```bash
git clone https://github.com/lopezyouhei/arxiv-mcp
cd arxiv-mcp
uv sync
```

## Wiring into Claude Desktop
### The easy way:

```bash
uv run mcp install server.py
```
### Manual config - edit `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "arxiv": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/arxiv-mcp", "run", "server.py"]
    }
  }
}
```

Config file locations:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`
- **Windows (standalone):** `%APPDATA%\Claude\claude_desktop_config.json`
- **Windows (Store version):** `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`
Fully quit and reopen Claude Desktop after editing. Closing the window isn't enough — the server runs as a subprocess that only launches at startup.
 
---

### Testing with the MCP Inspector

```bash
uv run mcp dev server.py
```

This opens a browser UI where you can call tools, read resources and invoke prompts directly without Claude in the loop. Useful for isolating whether a bug is in the server logic or in the client wiring.

Test order:
1. **Tools: `search_papers`** — confirms the server is running and arXiv is reachable
2. **Resource Templates: Read `arxiv://1706.03762`** — confirms template routing works
3. **Prompts: `summarize_for_layperson`** — confirms the prompt returns the expected string

Note: resource templates (`arxiv://{paper_id}`) appear under **Resource Templates**, not **List Resources**. Static resources (fixed URIs) appear in List Resources. They're different protocol calls.

---

## What I learned building this

- **The loop.** Claude Desktop launches your server as a subprocess at startup, they handshake, and then the model can call your tools mid-conversation. Restarting Claude Desktop isn't optional when you change code — it's re-launching the subprocess.
- **Type hints are the schema.** FastMCP reads your function signature and builds the tool's input schema from it. Your docstring is what the model reads to decide when to call the tool. Finally, enforcing function documentation!
- **Resources have two flavours.** Static resources appear in `resources/list`. Parameterised templates (`arxiv://{paper_id}`) appear in `resources/templates/list`.
- **Graceful failure is part of the design.** A tool that throws a raw exception gives the model garbage. A tool that returns `"arXiv is rate-limiting right now, try again in 10s"` lets the model recover on its own. The failure path is UX.
- **External content is untrusted.** See above (Prompt Injection).

---

## What's next

This is a throwaway project: local, stdio, no auth, no deployment. The point of this project was to learn the primitives.

Next: a **policy-agent server**, a billing support agent that handles customer refund requests. Sounds simple, but the design problems are not.

The main question is **where do you trust the model**.

The following architectural questions will be covered in this project:
- **Model judgment vs hard policy.** Some things the model should reason about: is this charge legitimate? Does the customer's explanation make sense? But other things must be deterministic, for example if a chargeback flag is present, *never* auto-refund, regardless of what the model concludes. That rule lives in code, not in a prompt. Prompts can be reasoned around; code can't.
- **Irreversible actions need idempotency.** If a refund tool gets called twice (network glitch, model retry), the customer shouldn't get refunded twice. The tool has to be safe to call multiple times with the same result.
- **Read and write are not the same trust level.** Reading a customer's account history is low-stakes. Issuing money is not. Those capabilities should be separate, with the irreversible one guarded.
- **Auth becomes real.** Anyone with a local stdio server can call its tools. A deployed service that issues refunds needs to know who's calling and whether they're allowed to.

**The technical gap it crosses:**
 
Streamable HTTP instead of stdio — deployed remotely, running independently, accessible to any MCP-compatible client with the right credentials. This is the step from "a tool that works for me locally" to "a service someone else can integrate." 

Follow along: [@lopez_youhei](https://x.com/lopez_youhei)
---
 
## Stack
 
- [FastMCP](https://github.com/modelcontextprotocol/python-sdk) — MCP server framework
- [arxiv](https://github.com/lukasschwab/arxiv.py) — arXiv API client
- [uv](https://astral.sh/uv) — Python toolchain

## License
 
MIT