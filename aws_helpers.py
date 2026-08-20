"""
Thin helpers around boto3 so the rest of the code never repeats AWS setup.

KEY IDEA -- the "default credential chain":
boto3 automatically looks for credentials in this order, and uses the first
it finds. We never hard-code keys anywhere:
  1. Environment variables
  2. ~/.aws/credentials  (this is what you fill in LOCALLY on Windows)
  3. The EC2 instance's attached IAM role (LabRole) -- used automatically ON EC2
So the identical code authenticates correctly both locally and on the server.
"""
import boto3
from botocore.config import Config
import config

# One shared session, pinned to our region.
_session = boto3.Session(region_name=config.AWS_REGION)

# Force modern SigV4 signing for S3 so presigned URLs use X-Amz-* params and
# always embed the temporary session token (required by Learner Lab creds).
_s3_config = Config(signature_version="s3v4")


# Cache clients/resources so we don't rebuild them on every call. Building a
# boto3 client is relatively expensive; the main page signs ~128 image URLs, so
# reusing one S3 client instead of creating 128 makes that page load fast.
_cache = {}


def dynamodb_resource():
    """High-level DynamoDB interface (nice Python dicts). Used for get/put/query."""
    if "ddb_res" not in _cache:
        _cache["ddb_res"] = _session.resource("dynamodb")
    return _cache["ddb_res"]


def dynamodb_client():
    """Low-level DynamoDB interface. Used for create_table / waiters."""
    if "ddb_cli" not in _cache:
        _cache["ddb_cli"] = _session.client("dynamodb")
    return _cache["ddb_cli"]


def s3_client():
    """Low-level S3 interface. Used for uploads and presigned URLs."""
    if "s3" not in _cache:
        _cache["s3"] = _session.client("s3", config=_s3_config)
    return _cache["s3"]


def table(name):
    """Shortcut: get a DynamoDB Table object by name."""
    return dynamodb_resource().Table(name)


def image_s3_key(img_url):
    """
    Derive the S3 object key from an image URL = its last path segment
    (the unique image hash). Songs that share album art share a key, so
    the same image is stored in S3 only once.
    Example: ".../ab67616d0000b273e21..." -> "ab67616d0000b273e21..."
    """
    return img_url.rsplit("/", 1)[-1]


def presigned_image_url(s3_key, ttl=None):
    """
    Turn an S3 object key into a temporary, signed HTTPS URL the browser can load
    directly -- WITHOUT making the bucket public. Returns None if there's no key.
    """
    if not s3_key:
        return None
    return s3_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": config.S3_BUCKET, "Key": s3_key},
        ExpiresIn=ttl or config.PRESIGNED_URL_TTL,
    )
