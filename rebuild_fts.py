import sqlite3

DB = "chatgpt.db"

con = sqlite3.connect(DB)
cur = con.cursor()

# Drop if exists (safe to run repeatedly)
cur.execute("DROP TABLE IF EXISTS messages_fts")

# FTS table with original message id stored (not indexed)
cur.execute("""
CREATE VIRTUAL TABLE messages_fts
USING fts5(
  content,
  message_id UNINDEXED,
  tokenize='unicode61'
)
""")

# Populate from messages (your schema: id TEXT PK, text TEXT)
cur.execute("""
INSERT INTO messages_fts(content, message_id)
SELECT text, id FROM messages
""")

con.commit()
print("✅ messages_fts rebuilt successfully.")