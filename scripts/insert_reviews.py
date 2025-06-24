#!/usr/bin/env python3
"""
Insert a CSV of reviews into ANY WordPress database.

• Works with any table prefix (`--prefix wp_`, `--prefix wp5_`, …)
• Lets you rename meta-keys (`--rating-key`, `--img-key`, `--verified-key`)
• All DB credentials come from CLI or env-vars.

Example:
    python insert_reviews.py reviews.csv 8348 \
        --host db.myhost.com --user wp --password secret --db wordpress
"""

from __future__ import annotations
import argparse, csv, sys
from datetime import datetime as dt
import pymysql

def cli(parser: argparse.ArgumentParser):
    parser.add_argument("csv_path", help="Path to CSV created by extract_reviews.py")
    parser.add_argument("post_id", type=int, help="ID of the WordPress post/product")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--user", default="root")
    parser.add_argument("--password", default="")
    parser.add_argument("--db", default="wordpress")
    parser.add_argument("--prefix", default="wp_", help="Table prefix")
    parser.add_argument("--rating-key", default="rating")
    parser.add_argument("--img-key", default="reviews-images")
    parser.add_argument("--verified-key", default="verified")
    parser.add_argument("--min-rating", type=float, default=0.0, help="Skip below this")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def insert(cursor, table: str, **values):
    cols = ", ".join(values)
    placeholders = ", ".join(["%s"] * len(values))
    sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
    cursor.execute(sql, tuple(values.values()))
    return cursor.lastrowid


def main(ns=None):
    if ns is None:
        ns = cli(argparse.ArgumentParser()).parse_args()

    conn = pymysql.connect(
        host=ns.host, user=ns.user, password=ns.password, database=ns.db, charset="utf8mb4"
    )
    cur = conn.cursor()
    comments_tbl = f"{ns.prefix}comments"
    meta_tbl = f"{ns.prefix}commentmeta"

    with open(ns.csv_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rating = float(row["rating"])
            if rating < ns.min_rating:
                continue

            # de-dup check
            cur.execute(
                f"""SELECT 1
                    FROM {comments_tbl} c
                    JOIN {meta_tbl} m ON m.comment_id = c.comment_ID
                    WHERE comment_post_ID=%s AND comment_author=%s
                      AND comment_date=%s AND m.meta_key=%s AND m.meta_value=%s""",
                (
                    ns.post_id,
                    row["author"],
                    row["date"],
                    ns.rating_key,
                    str(rating),
                ),
            )
            if cur.fetchone():
                continue

            if ns.dry_run:
                print("· Would insert comment from", row["author"])
                continue

            cid = insert(
                cur,
                comments_tbl,
                comment_post_ID=ns.post_id,
                comment_author=row["author"],
                comment_date=row["date"],
                comment_date_gmt=row["date"],
                comment_content=row["content"],
                comment_approved=1,
            )
            insert(cur, meta_tbl, comment_id=cid, meta_key=ns.rating_key, meta_value=rating)
            if row["photos"]:
                insert(cur, meta_tbl, comment_id=cid, meta_key=ns.img_key, meta_value=row["photos"])
            insert(cur, meta_tbl, comment_id=cid, meta_key=ns.verified_key, meta_value="1")

    if not ns.dry_run:
        conn.commit()
        print("✅ Done – committed!")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
