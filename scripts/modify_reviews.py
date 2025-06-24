#!/usr/bin/env python3
"""
Post-processing tool: update author names & anonymise low-rated reviews.
"""

from __future__ import annotations
import argparse, csv, random, sys
from faker import Faker
import pymysql

fake = Faker()

def cli(p):
    p.add_argument("csv_path")
    p.add_argument("--host", default="localhost")
    p.add_argument("--user", default="root")
    p.add_argument("--password", default="")
    p.add_argument("--db", default="wordpress")
    p.add_argument("--prefix", default="wp_")
    p.add_argument("--post-id", type=int, required=True)
    p.add_argument("--threshold", type=float, default=4.0, help="Update reviews < threshold")
    p.add_argument("--batch-size", type=int, default=200)
    p.add_argument("--dry-run", action="store_true")


def main(ns=None):
    if ns is None:
        ns = cli(argparse.ArgumentParser()).parse_args()

    conn = pymysql.connect(
        host=ns.host, user=ns.user, password=ns.password, database=ns.db, charset="utf8mb4"
    )
    cur = conn.cursor()
    comments_tbl = f"{ns.prefix}comments"

    with open(ns.csv_path, newline="", encoding="utf-8") as fh:
        to_update = [r for r in csv.DictReader(fh) if float(r["rating"]) < ns.threshold]

    random.shuffle(to_update)
    for chunk_idx in range(0, len(to_update), ns.batch_size):
        batch = to_update[chunk_idx : chunk_idx + ns.batch_size]
        for r in batch:
            new_name = fake.name()
            if ns.dry_run:
                print("· Would rename", r["author"], "→", new_name)
                continue
            cur.execute(
                f"""UPDATE {comments_tbl}
                    SET comment_author=%s
                    WHERE comment_post_ID=%s AND comment_author=%s AND comment_date=%s""",
                (new_name, ns.post_id, r["author"], r["date"]),
            )
        if not ns.dry_run:
            conn.commit()
            print("Committed batch", chunk_idx // ns.batch_size + 1)

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
