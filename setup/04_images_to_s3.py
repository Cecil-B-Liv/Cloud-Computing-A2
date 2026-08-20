"""
Task 2 -- Download every song image and upload it to S3.

- Creates the bucket (config.S3_BUCKET) if needed.
- Downloads each UNIQUE image once and uploads it under its s3_key.
- Skips images already present in S3, so re-running is quick.

The bucket stays PRIVATE; the web app serves images via presigned URLs.

Run:  .venv/Scripts/python.exe setup/04_images_to_s3.py
Idempotent.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests, botocore, config, aws_helpers


def ensure_bucket():
    s3 = aws_helpers.s3_client()
    try:
        s3.head_bucket(Bucket=config.S3_BUCKET)
        print(f"[=] Bucket '{config.S3_BUCKET}' already exists.")
        return
    except botocore.exceptions.ClientError:
        pass  # not found (or no access yet) -> try to create

    print(f"[+] Creating bucket '{config.S3_BUCKET}' ...")
    if config.AWS_REGION == "us-east-1":
        # us-east-1 is the default region: passing a LocationConstraint errors.
        s3.create_bucket(Bucket=config.S3_BUCKET)
    else:
        s3.create_bucket(
            Bucket=config.S3_BUCKET,
            CreateBucketConfiguration={"LocationConstraint": config.AWS_REGION},
        )
    s3.get_waiter("bucket_exists").wait(Bucket=config.S3_BUCKET)
    print(f"[+] Bucket '{config.S3_BUCKET}' created.")


def object_exists(s3, key):
    try:
        s3.head_object(Bucket=config.S3_BUCKET, Key=key)
        return True
    except botocore.exceptions.ClientError:
        return False


def upload_images():
    with open(config.DATA_FILE, encoding="utf-8") as f:
        songs = json.load(f)["songs"]

    # Deduplicate: map s3_key -> source image url.
    unique = {aws_helpers.image_s3_key(s["img_url"]): s["img_url"] for s in songs}
    print(f"[+] {len(songs)} songs -> {len(unique)} unique images to upload.")

    s3 = aws_helpers.s3_client()
    uploaded = skipped = 0
    for i, (key, url) in enumerate(sorted(unique.items()), 1):
        if object_exists(s3, key):
            skipped += 1
            continue
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        s3.put_object(
            Bucket=config.S3_BUCKET,
            Key=key,
            Body=resp.content,
            ContentType=resp.headers.get("Content-Type", "image/jpeg"),
        )
        uploaded += 1
        if i % 10 == 0 or i == len(unique):
            print(f"    ...{i}/{len(unique)} processed")
    print(f"[+] Uploaded {uploaded} new, skipped {skipped} already-present.")


if __name__ == "__main__":
    try:
        ensure_bucket()
        upload_images()
        print("\nSUCCESS: images are in S3.")
    except botocore.exceptions.ClientError as e:
        print("AWS ERROR:", e.response["Error"]["Code"], "-", e.response["Error"]["Message"])
        sys.exit(1)
    except requests.RequestException as e:
        print("DOWNLOAD ERROR:", e)
        sys.exit(1)
