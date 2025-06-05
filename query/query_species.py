import json
import os
import boto3
from typing import List, Tuple, Dict

REGION      = os.environ.get("AWS_REGION", "us-east-1")
TABLE_NAME  = os.environ.get("TABLE_NAME", "recognized_results")

dynamodb = boto3.client("dynamodb", region_name=REGION)

def build_filter(species: List[str]) -> Tuple[str, Dict[str, str]]:
    """
      attribute_exists(labels.#s0) AND attribute_exists(labels.#s1)
    FilterExpression  ExpressionAttributeNames
    """
    exprs, names = [], {}
    for idx, sp in enumerate(species):
        ph = f"#s{idx}"           
        exprs.append(f"attribute_exists(labels.{ph})")
        names[ph] = sp
    return " AND ".join(exprs), names

def lambda_handler(event, context):
    if event.get("httpMethod") == "GET":
        mvqs = event.get("multiValueQueryStringParameters") or {}
        species = mvqs.get("species", [])
    else:
        try:
            body = json.loads(event.get("body") or "{}")
            species = body.get("species", [])
        except json.JSONDecodeError:
            return _resp(400, {"error": "Invalid JSON body"})

    if not species:
        return _resp(400, {"error": "species list is required"})

    filter_exp, attr_names = build_filter(species)
    scan_params = {
        "TableName": TABLE_NAME,
        "FilterExpression": filter_exp,
        "ExpressionAttributeNames": attr_names
    }

    links, last_key = [], None
    while True:
        if last_key:
            scan_params["ExclusiveStartKey"] = last_key
        resp = dynamodb.scan(**scan_params)
        for item in resp.get("Items", []):
            bucket = item["bucket"]["S"]
            key    = item["id"]["S"]
            links.append(f"https://{bucket}.s3.amazonaws.com/{key}")
        last_key = resp.get("LastEvaluatedKey")
        if not last_key:
            break

    return _resp(200, {"links": links})


def _resp(status: int, body: dict):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body)
    }