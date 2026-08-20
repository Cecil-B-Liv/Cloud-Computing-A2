import boto3
from botocore.config import Config
import config

_session = boto3.Session(region_name=config.AWS_REGION)
# sigv4 so presigned urls include the temporary session token
_s3_config = Config(signature_version="s3v4")

# reuse clients instead of rebuilding them on every call
_cache = {}


def dynamodb_resource():
    if "ddb_res" not in _cache:
        _cache["ddb_res"] = _session.resource("dynamodb")
    return _cache["ddb_res"]


def dynamodb_client():
    if "ddb_cli" not in _cache:
        _cache["ddb_cli"] = _session.client("dynamodb")
    return _cache["ddb_cli"]


def s3_client():
    if "s3" not in _cache:
        _cache["s3"] = _session.client("s3", config=_s3_config)
    return _cache["s3"]


def table(name):
    return dynamodb_resource().Table(name)


def image_s3_key(img_url):
    # last path segment is the unique image hash -> use it as the S3 key
    return img_url.rsplit("/", 1)[-1]


def presigned_image_url(s3_key, ttl=None):
    if not s3_key:
        return None
    return s3_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": config.S3_BUCKET, "Key": s3_key},
        ExpiresIn=ttl or config.PRESIGNED_URL_TTL,
    )
