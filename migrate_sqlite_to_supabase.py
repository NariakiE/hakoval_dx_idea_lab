from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

from supabase import create_client


APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "hakoval_dx.db"
IMAGE_BUCKET = os.environ.get("SUPABASE_IMAGE_BUCKET", "idea-images")


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def fetch_rows(con: sqlite3.Connection, table: str) -> list[dict]:
    con.row_factory = sqlite3.Row
    return [dict(row) for row in con.execute(f"SELECT * FROM {table}").fetchall()]


def upload_image_if_needed(client, image_path: str) -> str:
    if not image_path or is_url(image_path):
        return image_path

    path = Path(image_path)
    if not path.exists():
        return image_path

    storage_path = f"ideas/{path.name}"
    content_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(path.suffix.lower(), "application/octet-stream")

    try:
        client.storage.from_(IMAGE_BUCKET).upload(
            storage_path,
            path.read_bytes(),
            file_options={"content-type": content_type, "upsert": "true"},
        )
    except Exception:
        pass
    return client.storage.from_(IMAGE_BUCKET).get_public_url(storage_path)


def main() -> None:
    supabase_url = os.environ["SUPABASE_URL"]
    supabase_key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    client = create_client(supabase_url, supabase_key)

    with sqlite3.connect(DB_PATH) as con:
        ideas = fetch_rows(con, "ideas")
        events = fetch_rows(con, "events")
        comments = fetch_rows(con, "comments")
        ratings = fetch_rows(con, "ratings")

    for idea in ideas:
        idea["image_path"] = upload_image_if_needed(client, idea.get("image_path", ""))

    if ideas:
        client.table("ideas").upsert(ideas).execute()
    if events:
        client.table("events").upsert(events).execute()
    if comments:
        client.table("comments").upsert(comments).execute()
    if ratings:
        client.table("ratings").upsert(ratings).execute()

    print(
        f"Migrated ideas={len(ideas)}, events={len(events)}, comments={len(comments)}, ratings={len(ratings)}"
    )


if __name__ == "__main__":
    main()

