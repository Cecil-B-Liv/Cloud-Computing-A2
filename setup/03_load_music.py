import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import botocore, config, aws_helpers


def load_music():
    with open(config.DATA_FILE, encoding="utf-8") as f:
        songs = json.load(f)["songs"]
    print(f"[+] read {len(songs)} songs from {config.DATA_FILE}")

    table = aws_helpers.table(config.MUSIC_TABLE)
    with table.batch_writer() as batch:
        for s in songs:
            batch.put_item(Item={
                "title": s["title"],
                "artist": s["artist"],
                "year": s["year"],
                "web_url": s["web_url"],
                "image_url": s["img_url"],
                "s3_key": aws_helpers.image_s3_key(s["img_url"]),
            })
    print(f"[+] wrote {len(songs)} items")


if __name__ == "__main__":
    try:
        load_music()
        print("\ndone")
    except botocore.exceptions.ClientError as e:
        print("AWS error:", e.response["Error"]["Code"], "-", e.response["Error"]["Message"])
        sys.exit(1)
