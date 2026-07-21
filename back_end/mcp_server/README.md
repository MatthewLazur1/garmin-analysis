# MCP Server

An [MCP](https://modelcontextprotocol.io) server that exposes this app's Garmin activity data, health metrics, and marathon plans as tools any MCP-compatible agent (Claude Desktop, Claude Code, a custom chat client) can call. This is **v1**: read-only. No tool here can modify a plan or write anything — that comes later, once RAG and a chat UI are in place.

---

## Purpose

The long-term goal (see the [main README](../../README.md)) is an AI coach that can answer questions like "what's on my plan this week" or "how's my recovery looking" by pulling real data instead of guessing. This server is the data-access layer for that: it wraps the existing `ReportManager` / `ReportBuilder` / `ReportReader` classes as MCP tools, so any agent — not just this app's own future chat tab — can query them over a standard protocol.

It does not itself talk to an LLM. It's purely the tool-serving side; something else (Claude Desktop, Claude Code, or a Tool-Runner-based agent we build later) is the client that calls these tools.

---

## Structure

```
mcp_server/
├── app.py             # The shared FastMCP instance. Deliberately isolated — see "Why app.py is separate" below.
├── server.py           # Entrypoint: imports app + tool modules, runs mcp.run() over stdio.
├── context.py          # Lazy singletons: Garmin client (authenticates once, reused), ReportManager, ReportBuilder.
├── plan_tools.py        # Tools backed by Supabase (marathon plans).
├── garmin_tools.py      # Tools backed by the Garmin Connect API.
├── rag_tools.py         # rag_search tool, backed by ../rag/ (Voyage AI + Supabase pgvector).
└── serialization.py     # DataFrame -> JSON-safe dict/list conversion (numpy types, NaN, timestamps).
```

`rag_tools.py` is deliberately thin — the embedding/search/ingestion logic lives in `back_end/rag/` (a sibling of `mcp_server/`, not inside it) because ingestion is a standalone offline job (`python -m back_end.rag.ingest`), not something the running server does.

### Why `app.py` is separate from `server.py`

`plan_tools.py` and `garmin_tools.py` need to import the shared `mcp` object to register their tools via `@mcp.tool()`. If that object lived in `server.py`, running the server as `python -m back_end.mcp_server.server` would load `server.py` **twice** — once as `__main__`, once as `back_end.mcp_server.server` (because the tool modules import it by that dotted path) — creating two separate `FastMCP` instances. The tools register on the second one; the running server (`__main__`'s copy) never sees them and reports zero tools. This actually happened during development. Keeping the shared instance in its own `app.py`, which is never the entrypoint, makes the bug structurally impossible rather than something to remember to avoid.

---

## Tools (v1 — all read-only)

| Tool | Backed by | Notes |
|---|---|---|
| `list_marathon_plans()` | Supabase (`ReportManager.list_plans`) | Returns plan names |
| `get_marathon_plan(name)` | Supabase (`ReportManager.load_plan`) | Full week-by-week breakdown; returns `{"found": false, "name": ...}` if it doesn't exist — never an empty/ambiguous response |
| `get_weekly_mileage(start_date, end_date)` | Garmin (`ReportBuilder.aggregate_weekly_mileage`) | Dates as `YYYY-MM-DD` |
| `get_personal_records()` | Garmin (`ReportBuilder.get_all_time_prs`) | 5K / 10K / Half / Marathon |
| `list_activities(start_date, end_date)` | Garmin (`ReportBuilder.list_activities`) | Per-activity summaries; also how the agent discovers `activity_id`s |
| `get_activity_detail(activity_id)` | Garmin (`ReportBuilder.get_activity_summary`) | Single activity, by ID from `list_activities` |
| `get_health_snapshot(target_date)` | Garmin (`ReportBuilder.get_health_snapshot`) | Sleep score, HRV, resting HR for one date |
| `rag_search(query, top_k=5)` | Voyage AI + Supabase `pgvector` | Semantic search over embedded reference docs (training/coaching methodology, sports science); returns `{source, content, metadata, similarity}` per match. Empty list if nothing's been ingested yet. |

## Credential handling

`context.py` authenticates to Garmin **lazily** — only on the first tool call that needs it — and caches the client for the life of the server process, so a whole chat session doesn't re-authenticate per tool call. Credentials (`GARMIN_EMAIL`, `GARMIN_PASSWORD`, `SUPABASE_DB_URL`, `OPENWEATHERMAP_API_KEY`, `VOYAGE_API_KEY`) come from `garmin-analysis/.env`, loaded via `back_end/__init__.py` using a path derived from the package location — **not** from the process's working directory, since MCP clients (Claude Desktop, Inspector, etc.) don't `cd` into this project before launching the server.

## RAG: embedding reference documents

`rag_search` reads from a `document_chunks` table in Supabase (`pgvector` extension, `vector(1024)` column, HNSW cosine index) — see `back_end/rag/rag_repository.py` for the schema. Nothing is embedded automatically; you populate the index by dropping `.txt`/`.md`/`.pdf` files into `rag_docs/` (see its own README) and running:

```bash
uv run --project /Users/matthewlazur/garmin-performance/garmin-analysis python -m back_end.rag.ingest
```

This chunks each file (`back_end/rag/chunking.py`, paragraph-aware, ~1200 chars with overlap), embeds the chunks via Voyage AI (`voyage-3`, `input_type="document"`), and replaces that file's chunks in Supabase — so re-running after an edit is safe. `rag_search` embeds the query with `input_type="query"` and ranks by cosine similarity. Requires `VOYAGE_API_KEY` (get one at [voyageai.com](https://voyageai.com)).

---

## How to run it

```bash
uv run garmin-mcp
```

Runs over **stdio** — it's not a network server; an MCP client spawns it as a subprocess and talks to it over stdin/stdout. Because of that, always launch it with an explicit `--project` path rather than relying on cwd, since real clients invoke it from wherever *they* happen to run:

```bash
uv run --project /Users/matthewlazur/garmin-performance/garmin-analysis garmin-mcp
```

## How to test it

**MCP Inspector** (visual, browser-based — recommended first pass after any change):

```bash
npx @modelcontextprotocol/inspector uv run --project /Users/matthewlazur/garmin-performance/garmin-analysis garmin-mcp
```

Opens `http://localhost:6274`. Lists all 8 tools; fill in parameters and click **Run Tool** to see the live JSON response. (Needs Node.js — `brew install node` if you don't have it.)

**Claude Code:**

```bash
claude mcp add garmin-performance -- uv run --project /Users/matthewlazur/garmin-performance/garmin-analysis garmin-mcp
```

Then just ask Claude Code things like "what's my 5K PR" in any session.

**Claude Desktop** — add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "garmin-performance": {
      "command": "uv",
      "args": ["run", "--project", "/Users/matthewlazur/garmin-performance/garmin-analysis", "garmin-mcp"]
    }
  }
}
```

Restart Claude Desktop afterward.

**Programmatic** — spin up a real MCP client session in Python via `mcp.ClientSession` + `mcp.client.stdio.stdio_client`, `await session.call_tool(name, args)`. Useful for scripted checks; there's no permanent test suite for this yet (see "What's next").

---

## What's next

Per the project's phased roadmap:

1. ~~**RAG** — embed reference documents (Voyage AI embeddings into Supabase `pgvector`) and add a `rag_search` tool alongside these.~~ Done — see "RAG: embedding reference documents" above. Still needs real reference docs ingested (`rag_docs/` is currently empty) and a `VOYAGE_API_KEY`.
2. **Chat integration** — wire this server into a new "Coach" tab in the Streamlit app, using the Anthropic SDK's Tool Runner (with its MCP conversion helpers) to drive an actual agent loop against these tools.
3. **Write tools** — once the read path and RAG are proven, add plan-drafting tools (e.g. `draft_marathon_plan`) that stage a proposed plan for review rather than writing directly — kept separate and later deliberately, so the agent never mutates a real plan without the user seeing it first.
4. **Automated tests** — the Inspector/programmatic checks above are manual; a real test suite (pytest fixtures that fake the Garmin client, Voyage client, and Supabase engine) would let tool changes be verified without hitting live APIs every time.
