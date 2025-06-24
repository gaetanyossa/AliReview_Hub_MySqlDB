#!/usr/bin/env python3
"""
Bulk-replace a given author name (or regex) with random realistic names.
"""

import argparse, re, sys
from faker import Faker
import pymysql

fake = Faker()

def cli(p):
    p.add_argument("--match", default=r"AliExpress Shopper", help="Exact string or regex")
    p.add_argument("--host", default="localhost")
    p.add_argument("--user", default="root")
    p.add_argument("--password", default="")
    p.add_argument("--db", default="wordpress")
    p.add_argument("--prefix", default="wp_")
    p.add_argument("--dry-run", action="store_true")


def main(ns=None):
    if ns is None:
        ns = cli(argparse.ArgumentParser()).parse_args()

    conn = pymysql.connect(
        host=ns.host, user=ns.user, password=ns.password, database=ns.db, charset="utf8mb4"
    )
    cur = conn.cursor()
    comments_tbl = f"{ns.prefix}comments"

    cur.execute(f"SELECT comment_ID, comment_author FROM {comments_tbl}")
    pattern = re.compile(ns.match, re.I)
    for cid, author in cur.fetchall():
        if not pattern.search(author):
            continue
        new_name = fake.name()
        if ns.dry_run:
            print("· Would rename", author, "→", new_name)
            continue
        cur.execute(
            f"UPDATE {comments_tbl} SET comment_author=%s WHERE comment_ID=%s",
            (new_name, cid),
        )

    if not ns.dry_run:
        conn.commit()
        print("✅ Author names updated.")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
