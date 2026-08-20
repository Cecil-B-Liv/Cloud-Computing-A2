"""
Task 1.3 -- Load all songs from the JSON file into the "music" table.

Each song becomes one item with the spec's attributes:
    title, artist, year, web_url, image_url
plus s3_key (the S3 object key for that song's image, set now so the
music item is complete; script 04 uploads the actual image bytes).

Run:  .venv/Scripts/python.exe setup/03_load_music.py
Idempotent (put_item overwrites, so re-running just refreshes the data).
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import botocore, config, aws_helpers


def load_music():
    with open(config.DATA_FILE, encoding="utf-8") as f:
        songs = json.load(f)["songs"]
    print(f"[+] Loaded {len(songs)} songs from {config.DATA_FILE}")

    table = aws_helpers.table(config.MUSIC_TABLE)
    # batch_writer buffers and sends items in batches of 25 automatically.
    with table.batch_writer() as batch:
        for s in songs:
            batch.put_item(Item={
                "title": s["title"],
                "artist": s["artist"],
                "year": s["year"],            # kept as string, matching the JSON
                "web_url": s["web_url"],
                "image_url": s["img_url"],     # JSON's img_url -> spec's image_url
                "s3_key": aws_helpers.image_s3_key(s["img_url"]),
            })
    print(f"[+] Wrote {len(songs)} items into '{config.MUSIC_TABLE}'.")


if __name__ == "__main__":
    try:
        load_music()
        print("\nSUCCESS: music table loaded.")
    except botocore.exceptions.ClientError as e:
        print("AWS ERROR:", e.response["Error"]["Code"], "-", e.response["Error"]["Message"])
        sys.exit(1)
