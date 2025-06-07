# Step-by-step Guide to Build: Find Images and Videos Based on Tags API (GET/POST via API Gateway)

## ✅ Step 1: Lambda Function Code (query_tags_lambda.py)

import json
import boto3
import os
from urllib.parse import unquote_plus

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get("TABLE_NAME", "recognized_results")
table = dynamodb.Table(table_name)


def lambda_handler(event, context):
    if event["httpMethod"] == "GET":
        params = event.get("queryStringParameters", {}) or {}
        tags = extract_tags_from_get(params)
    elif event["httpMethod"] == "POST":
        body = json.loads(event["body"])
        tags = body.get("tags", {})
    else:
        return {"statusCode": 405, "body": json.dumps("Method Not Allowed")}

    matched_urls = []
    scan = table.scan()
    for item in scan.get("Items", []):
        labels = parse_labels(item.get("labels"))
        if all(labels.get(tag, 0) >= count for tag, count in tags.items()):
            file_id = item["id"]
            bucket = item["bucket"]
            url = generate_s3_url(bucket, file_id)
            matched_urls.append(url)

    return {
        "statusCode": 200,
        "body": json.dumps({"links": matched_urls})
    }


def parse_labels(labels):
    if isinstance(labels, dict) and "M" in labels:
        # DynamoDB JSON format
        return {k: int(v["N"]) for k, v in labels["M"].items()}
    return labels  # already native


def generate_s3_url(bucket, key):
    return f"https://{bucket}.s3.amazonaws.com/{key}"


def extract_tags_from_get(params):
    tags = {}
    i = 1
    while True:
        tag_key = params.get(f"tag{i}")
        count_key = params.get(f"count{i}")
        if not tag_key or not count_key:
            break
        try:
            tags[unquote_plus(tag_key)] = int(count_key)
        except ValueError:
            pass
        i += 1
    return tags
