#!/usr/bin/env python3
"""
Search and export from chatgpt.db (built by build_chatgpt_db.py).

Usage:
  python search_chatgpt_db.py chatgpt.db --q "verizon refund" --limit 20
  python search_chatgpt_db.py chatgpt.db --q "title:verizon AND role:user" --since 2025-01-01 --csv hits.csv
"""
import argparse, sqlite3, csv, sys, datetime

def parse_date(s):
    return datetime.datetime.fromisoformat(s).timestamp()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("db")
    p.add_argument("--q", default="", help="FTS query. Examples: verizon, 'refund NEAR/5 charge', role:assistant")
    p.add_argument("--since", help="Start date (YYYY-MM-DD)")
    p.add_argument("--until", help="End date (YYYY-MM-DD)")
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--csv", help="Optional CSV export path")
    args = p.parse_args()

    conn = sqlite3.connect(args.db)
    c = conn.cursor()

    where = []
    params = []
    if args.q:
        q = args.q.replace("role:", "author_role:")
        where.append("messages_fts MATCH ?")
        params.append(q)
    if args.since:
        where.append("m.created_at >= ?")
        params.append(parse_date(args.since))
    if args.until:
        where.append("m.created_at <= ?")
        params.append(parse_date(args.until))

    sql = f"""
    SELECT m.id, m.conversation_id, c.title, m.author_role, m.created_at, m.text
    FROM messages_fts f
    JOIN messages m ON m.id = f.message_id
    JOIN conversations c ON c.id = m.conversation_id
    {("WHERE " + " AND ".join(where)) if where else ""}
    ORDER BY m.created_at ASC
    LIMIT ?
    """
    params.append(args.limit)

    rows = c.execute(sql, params).fetchall()

    def ts_to_iso(ts):
        if ts is None: return ""
        return datetime.datetime.fromtimestamp(ts).isoformat(sep=" ", timespec="seconds")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["message_id","conversation_id","title","role","created_at","text"])
            for r in rows:
                w.writerow([r[0], r[1], r[2], r[3], ts_to_iso(r[4]), r[5]])
        print(f"Wrote {len(rows)} rows to {args.csv}")
    else:
        for r in rows:
            print(f"[{ts_to_iso(r[4])}] ({r[3]}) {r[2]}")
            print(r[5][:500].replace("\n"," "))
            print("-"*80)

if __name__ == "__main__":
    main()
