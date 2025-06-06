import json, re, boto3, os
from urllib.parse import urlparse, unquote_plus

s3        = boto3.client("s3")
dynamodb  = boto3.resource("dynamodb")
TABLE     = dynamodb.Table(os.getenv("TABLE_NAME", "recognized_results"))

IMG_EXT   = (".jpg", ".jpeg", ".png", ".bmp", ".webp")   # The suffix "thumbnail" is needed

URL_RE = re.compile(r"https?://([^/]+)\.s3[^/]+/(.+)")

def lambda_handler(event, _ctx):
    """POST body: { "urls": [url1, url2, ...] }"""
    try:
        body = json.loads(event.get("body", "{}"))
        urls = body.get("urls", [])
        if not urls:
            return _resp(400, "No URLs provided.")

        delete_items = []      # <bucket, key> 
        db_keys      = []      # DynamoDB 

        for url in urls:
            m = URL_RE.match(url)
            if not m:
                continue
            bucket, key = m.group(1), unquote_plus(m.group(2))
            delete_items.append({"Bucket": bucket, "Key": key})
            db_keys.append({"id": key})

            # If it is the original image and it is a picture => add thumbnail
            if not key.startswith("thumbnail/") and key.lower().endswith(IMG_EXT):
                thumb_key = f"thumbnail/{os.path.basename(key)}"
                delete_items.append({"Bucket": bucket, "Key": thumb_key})

        # Batch deletion of S3 (grouping per bucket, 1000 items per batch)
        _delete_s3_batch(delete_items)

        # Cut off DynamoDB
        _delete_dynamo_batch(db_keys)

        return _resp(200, f"Deleted objects: {len(delete_items)} ; db rows: {len(db_keys)}")

    except Exception as e:
        return _resp(500, f"Error: {e}")

# ──────────────────────────────────────────────
def _delete_s3_batch(objs):
    from itertools import groupby
    objs.sort(key=lambda x: x["Bucket"])
    for bucket, group in groupby(objs, key=lambda x: x["Bucket"]):
        chunk = []
        for item in group:
            chunk.append({"Key": item["Key"]})
            if len(chunk) == 1000:
                s3.delete_objects(Bucket=bucket, Delete={"Objects": chunk})
                chunk = []
        if chunk:
            s3.delete_objects(Bucket=bucket, Delete={"Objects": chunk})

def _delete_dynamo_batch(keys):
    with TABLE.batch_writer() as batch:
        for k in keys:
            batch.delete_item(Key=k)

def _resp(code, msg):
    return {"statusCode": code,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": msg})}
