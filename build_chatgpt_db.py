#!/usr/bin/env python3
"""
Build a SQLite database (chatgpt.db) from ChatGPT export 'conversations.json'.
Creates normalized tables + an FTS5 index for fast full-text search.

Usage:
  python build_chatgpt_db.py "C:\path\to\conversations.json" --out chatgpt.db

Optional flags:
  --max-msgs N       Limit messages per conversation (for testing)
  --title-filter STR Only include conversations whose title contains STR (case-insensitive)
"""
import argparse, json, os, sqlite3, hashlib, re
from datetime import datetime, timezone

def iso_to_ts(iso_or_unix):
    if iso_or_unix is None:
        return None
    if isinstance(iso_or_unix, (int, float)):
        return float(iso_or_unix)
    try:
        return datetime.fromisoformat(str(iso_or_unix).replace("Z","+00:00")).timestamp()
    except Exception:
        return None

def extract_text(message: dict) -> str:
    if not message:
        return ""
    content = message.get("content")
    if isinstance(content, dict):
        parts = content.get("parts")
        if isinstance(parts, list):
            return "\n".join(p if isinstance(p, str) else "" for p in parts)
        if isinstance(content.get("text"), str):
            return content["text"]
    if isinstance(message.get("text"), str):
        return message["text"]
    return ""

def is_real(message: dict) -> bool:
    if not message:
        return False
    role = (message.get("author") or {}).get("role")
    txt = extract_text(message).strip()
    return bool(txt) and role in ("user", "assistant")

def linearize(mapping: dict):
    nodes = []
    for _, node in mapping.items():
        m = node.get("message")
        if m and is_real(m):
            ct = m.get("create_time") or m.get("create_time_iso") or m.get("update_time")
            nodes.append((ct, m))
    def key(item):
        ct = item[0]
        if ct is None:
            return 0.0
        if isinstance(ct, (int, float)):
            return float(ct)
        try:
            return datetime.fromisoformat(str(ct).replace("Z","+00:00")).timestamp()
        except Exception:
            return 0.0
    nodes.sort(key=key)
    return [m for _, m in nodes]

def ensure_schema(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.executescript("""
    PRAGMA journal_mode = WAL;
    PRAGMA synchronous = NORMAL;

    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        title TEXT,
        created_at REAL,
        updated_at REAL
    );

    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        author_role TEXT,
        created_at REAL,
        text TEXT,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
    );

    CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
        text, author_role, conversation_id, message_id, created_at, 
        content='',
        tokenize='porter'
    );

    CREATE VIEW IF NOT EXISTS v_messages AS
      SELECT m.id as message_id, m.conversation_id, c.title, m.author_role, m.created_at, m.text
      FROM messages m JOIN conversations c ON m.conversation_id = c.id;
    """)
    conn.commit()

def upsert_conversation(cur, conv_id, title, created_at, updated_at):
    cur.execute("""
        INSERT INTO conversations (id, title, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          title=excluded.title,
          created_at=COALESCE(conversations.created_at, excluded.created_at),
          updated_at=excluded.updated_at
    """, (conv_id, title, created_at, updated_at))

def insert_message(cur, msg_id, conv_id, role, created_at, text):
    cur.execute("""
        INSERT OR REPLACE INTO messages (id, conversation_id, author_role, created_at, text)
        VALUES (?, ?, ?, ?, ?)
    """, (msg_id, conv_id, role, created_at, text))
    cur.execute("""
        INSERT INTO messages_fts (rowid, text, author_role, conversation_id, message_id, created_at)
        VALUES (NULL, ?, ?, ?, ?, ?)
    """, (text, role or "", conv_id, msg_id, created_at or 0))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("conversations_json")
    p.add_argument("--out", default="chatgpt.db")
    p.add_argument("--max-msgs", type=int, default=None)
    p.add_argument("--title-filter", type=str, default=None)
    args = p.parse_args()

    data = json.load(open(args.conversations_json, "r", encoding="utf-8"))
    if isinstance(data, dict) and "conversations" in data:
        conversations = data["conversations"]
    elif isinstance(data, list):
        conversations = data
    else:
        raise SystemExit("Unrecognized conversations.json format")

    if args.title_filter:
        needle = args.title_filter.lower()
        conversations = [c for c in conversations if (c.get("title") or "").lower().find(needle) >= 0]

    conn = sqlite3.connect(args.out)
    ensure_schema(conn)
    cur = conn.cursor()

    for conv in conversations:
        conv_id = conv.get("id") or hashlib.sha1((conv.get("title") or "").encode("utf-8")).hexdigest()
        title = conv.get("title") or "Conversation"
        mapping = conv.get("mapping") or {}
        msgs = linearize(mapping)
        if args.max_msgs is not None:
            msgs = msgs[:args.max_msgs]

        created_at = iso_to_ts(msgs[0].get("create_time")) if msgs else None
        updated_at = iso_to_ts(msgs[-1].get("create_time")) if msgs else None
        upsert_conversation(cur, conv_id, title, created_at, updated_at)

        for m in msgs:
            role = (m.get("author") or {}).get("role")
            ts = iso_to_ts(m.get("create_time"))
            text = extract_text(m)
            msg_id = m.get("id") or hashlib.sha1(f"{conv_id}:{ts}:{role}:{text[:32]}".encode("utf-8")).hexdigest()
            insert_message(cur, msg_id, conv_id, role, ts, text)

    conn.commit()
    conn.close()
    print(f"Built {args.out} with {len(conversations)} conversation(s).")

if __name__ == "__main__":
    main()
