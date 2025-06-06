# Assumption: users can only send the s3-url of existing files 
# as a part of the request to query any other files with the same labels.

"""
request body example:

thumbnail_url: s3://team163-bucket/thumbnail/crows_1.jpg
{
  "httpMethod": "POST",
  "body": "{\"thumbnail_url\": \"{thumbnail_url}\"}"
}

response body example:
{
    "statusCode": 200, 
    "headers":
    {
        "Content-Type": "application/json"
    },
    "body":
    "{
        \"detected_labels\": [\"Pigeon\", \"Crow\"],
        \"query_by_species_result\": 
        {
            \"links\":
            [
                \"https://team163-bucket.s3.amazonaws.com/crows.mp4\",
                \"https://team163-bucket.s3.amazonaws.com/image/crows_1.jpg\"
            ]
        }
    }"
}

"""

import json
import boto3
import urllib.parse

dynamodb = boto3.client("dynamodb")
lambda_client = boto3.client("lambda")
table_name = "recognized_results"
query_function = "query_by_species"

def lambda_handler(event, context):
    if event.get("httpMethod") != "POST":
        return response_json(405, {"error": "Method Not Allowed. Use POST."})

    try:
        body = json.loads(event.get("body", "{}"))
        media_url = body.get("media_url")
        if not media_url:
            return response_json(400, {"error": "Missing 'media_url'"})
    except json.JSONDecodeError:
        return response_json(400, {"error": "Invalid JSON body"})

    try:
        # extract the key from the url
        parsed = urllib.parse.urlparse(media_url)
        key = parsed.path.lstrip("/")

        if not (key.startswith("image/") or key.startswith("videos/") or key.startswith("audios/")):
            return response_json(400, {"error": "File must be under image/, videos/, or audios/ folder."})

        # get response of  detection result from dynamodb
        response = dynamodb.get_item(
            TableName=table_name,
            Key={"id": {"S": key}}
        )

        item = response.get("Item")
        if not item:
            return response_json(404, {"error": "No detection result found."})

        # extract label names
        labels_attr = item.get("labels", {})
        if "M" not in labels_attr:
            return response(500, {"error": "Invalid labels format in database"})

        raw_labels = labels_attr["M"]
        labels = list(raw_labels.keys())

        # build payload for query_by_species
        species_query_event = {
            "httpMethod": "GET",
            "queryStringParameters": None,
            "multiValueQueryStringParameters": {
                "species": labels
            },
            "headers": {},
            "body": None
        }

        # invoke query_by_species to query species
        response = lambda_client.invoke(
            FunctionName=query_function,
            InvocationType='RequestResponse',
            Payload=json.dumps(species_query_event)
        )

        query_result = json.loads(response['Payload'].read())

        return response_json(200, {
            "detected_labels": labels,
            "query_by_species_result": json.loads(query_result.get("body", "{}"))
        })

    except Exception as e:
        return response_json(500, {"error": str(e)})
    
def response_json(status: int, body: dict):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body)
    }
