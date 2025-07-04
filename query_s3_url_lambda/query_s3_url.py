import json
import boto3

def lambda_handler(event, context):
    # Here, it is assumed that the front-end POST {"s3_url": "s3://bucket/key"}
    try:
        body = json.loads(event.get('body', '{}'))
        s3_url = body.get('s3_url', '')
    except Exception:
        return {"statusCode": 400, "body": "Invalid input format."}

    # Parse s3_url
    if not s3_url.startswith("s3://"):
        return {"statusCode": 400, "body": "Invalid s3_url format"}
    _, bucket, *key_parts = s3_url.split('/')
    bucket = bucket.strip()
    key = '/'.join(key_parts)

    s3 = boto3.client('s3')
    try:
        # Check if the file exists and obtain the metadata
        resp = s3.head_object(Bucket=bucket, Key=key)
        result = {
            "file_name": key,
            "size": resp['ContentLength'],
            "content_type": resp.get('ContentType', ''),
            "last_modified": str(resp['LastModified'])
        }
        return {"statusCode": 200, "body": json.dumps(result)}
    except Exception as e:
        return {"statusCode": 404, "body": f"File not found: {str(e)}"}
