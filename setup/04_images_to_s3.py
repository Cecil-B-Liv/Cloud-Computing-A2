import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests, botocore, config, aws_helpers


def ensure_bucket():
    s3 = aws_helpers.s3_client()
    try:
        s3.head_bucket(Bucket=config.S3_BUCKET)
        print(f"[=] bucket '{config.S3_BUCKET}' already exists")
        return
    except botocore.exceptions.ClientError:
        pass

    print(f"[+] creating bucket '{config.S3_BUCKET}'")
    if config.AWS_REGION == "us-east-1":
        # us-east-1 must NOT get a LocationConstraint
        s3.create_bucket(Bucket=config.S3_BUCKET)
    else:
        s3.create_bucket(
            Bucket=config.S3_BUCKET,
            CreateBucketConfiguration={"LocationConstraint": config.AWS_REGION},
        )
    s3.get_waiter("bucket_exists").wait(Bucket=config.S3_BUCKET)
    print("[+] bucket created")


def object_exists(s3, key):
    try:
        s3.head_object(Bucket=config.S3_BUCKET, Key=key)
        return True
    except botocore.exceptions.ClientError:
        return False


def upload_images():
    with open(config.DATA_FILE, encoding="utf-8") as f:
        songs = json.load(f)["songs"]

    # dedupe by s3 key so shared album art is uploaded once
    unique = {aws_helpers.image_s3_key(s["img_url"]): s["img_url"] for s in songs}
    print(f"[+] {len(songs)} songs -> {len(unique)} unique images")

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
            print(f"    {i}/{len(unique)}")
    print(f"[+] uploaded {uploaded}, skipped {skipped}")


if __name__ == "__main__":
    try:
        ensure_bucket()
        upload_images()
        print("\ndone")
    except botocore.exceptions.ClientError as e:
        print("AWS error:", e.response["Error"]["Code"], "-", e.response["Error"]["Message"])
        sys.exit(1)
    except requests.RequestException as e:
        print("download error:", e)
        sys.exit(1)
