# ChatGPT -> SQLite Database (with FTS5 search)

This kit turns your exported `conversations.json` into a searchable SQLite DB (`chatgpt.db`) and gives you a small CLI to query and export results.

## Files
- build_chatgpt_db.py — build `chatgpt.db` from `conversations.json`.
- search_chatgpt_db.py — quick search/export tool.
- Output DB: `chatgpt.db` with tables: conversations, messages, and FTS index `messages_fts`.

## Build the database
Windows PowerShell example:
    python build_chatgpt_db.py "C:\path\to\conversations.json" --out chatgpt.db

Optional flags:
    --title-filter "verizon"   # only include matching conversation titles
    --max-msgs 500             # cap per-conversation messages

## Search examples
Basic keyword:
    python search_chatgpt_db.py chatgpt.db --q "verizon refund" --limit 20

Near match (words within 5 terms):
    python search_chatgpt_db.py chatgpt.db --q "verizon NEAR/5 refund"

By role (assistant only):
    python search_chatgpt_db.py chatgpt.db --q "role:assistant"

Date range:
    python search_chatgpt_db.py chatgpt.db --q "verizon" --since 2025-01-01 --until 2025-08-30

Export to CSV:
    python search_chatgpt_db.py chatgpt.db --q "lawsuit OR affidavit" --csv hits.csv

## Schema
- conversations(id TEXT PRIMARY KEY, title TEXT, created_at REAL, updated_at REAL)
- messages(id TEXT PRIMARY KEY, conversation_id TEXT, author_role TEXT, created_at REAL, text TEXT)
- messages_fts(text, author_role, conversation_id, message_id, created_at) — FTS5 index

## Notes
- 100% local, no internet required.
- Uses SQLite FTS5 for fast full-text search with stemming.
- Timestamps are stored as UNIX epoch seconds; the search tool prints human time.
