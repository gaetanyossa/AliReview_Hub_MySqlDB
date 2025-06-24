#!/usr/bin/env python3
"""
Search & replace any word/phrase inside **comment_content**.

Example:
    python replace_word.py --search aliexpress --replace MyStore \
        --host localhost --db wordpress
"""

import argparse, pymysql, sys, re

def cli(p):
    p.add_argument("--search", required=True, help="String or regex to search")
    p.add_argument("--replace", required=True, help="Replacement string")
    p.add_argument("--host", default="localhost")
    p.add_argument("--user", default="root")
    p.add_argument("--password", default="")
    p.add_argument("--db", default="wordpress")
    p.add_argument("--prefix", default="wp_")
    p.add_argument("--dry-run", action="store_true")


def main(ns=None):
    if ns is None:
        ns = cli(argparse.ArgumentParser()).parse_args()

    pattern = re.compile(ns.search, re.I)
    conn = pymysql.connect(
        host=ns.host, user=ns.user, password=ns.password, database=ns.db, charset="utf8mb4"
    )
    cur = conn.cursor()
    tbl = f"{ns.prefix}comments"
    cur.execute(f"SELECT comment_ID, comment_content FROM {tbl}")
    for cid, content in cur.fetchall():
        new_content = pattern.sub(ns.replace, content)
        if new_content == content:
            continue
        if ns.dry_run:
            print(f"· Would patch comment {cid}")
            continue
        cur.execute(f"UPDATE {tbl} SET comment_content=%s WHERE comment_ID=%s", (new_content, cid))

    if not ns.dry_run:
        conn.commit()
        print("✅ Content patched.")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
