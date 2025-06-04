import json
import boto3
import os
from urllib.parse import urlparse
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get("TABLE_NAME", "recognized_results")
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    # TODO implement
    if event["httpMethod"] != "POST":
         return {
            'statusCode': 405,
            'body': json.dumps('Method Not Allowed')
        }
    body = json.loads(event['body'])
    url = body["url"]
    keys = list(map(s3_url_to_key, url))
    operation = body["operation"]
    tags = body["tags"]

    for key in keys:
        response = table.get_item(Key={'id': key})
        if 'Item' not in response:
            print(f"Item with key '{key}' not found.")
            continue

        item = response['Item']
        if 'labels' not in item:
            item['labels'] = {}

        for tag, count in tags.items():
            current = item['labels'].get(tag, 0)
            if operation == 1:
                item['labels'][tag] = current + count

            elif operation == 0:
                item['labels'][tag] = max(0, current - count)
                if item['labels'][tag] == 0:
                    del item['labels'][tag]
        table.put_item(Item=item)
    return {
        'statusCode': 200,
        'body': json.dumps('tags updated!')
    }

def s3_url_to_key(s3_url):
    """Extract the object key from an S3 URL."""
    parsed = urlparse(s3_url)
    return parsed.path.lstrip('/')