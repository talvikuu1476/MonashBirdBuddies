# Assumption: user only sends 1 thumbnail url for each request

"""
request body example:

thumbnail_url: s3://team163-bucket/thumbnail/crows_1.jpg
{
  "httpMethod": "POST",
  "body": "{\"thumbnail_url\": \"{thumbnail_url}\"}"
}

response body example:
{"statusCode": 200, "body": "{\"full_image_url\": \"https://team163-bucket.s3.amazonaws.com/image/crows_1.jpg\"}"}

"""

import json
import urllib.parse

table_name = "recognized_results"

def lambda_handler(event, context):
    bucket_name = "team163-bucket"
    
    if event["httpMethod"] != "POST":
        return {
            'statusCode': 405,
            'body': json.dumps("Only POST Method is Allowed")
        }
    
    try:
        body = json.loads(event["body"])
        thumbnail_url = body.get("thumbnail_url")
        
        if not thumbnail_url:
            return {
                'statusCode': 400,
                'body': json.dumps("The s3-url is missing")
            }
            
        parsed_url = urllib.parse.urlparse(thumbnail_url)
        key = parsed_url.path.lstrip('/')
        
        if not key:
            return {
                'statusCode': 400,
                'body': json.dumps("The s3-url is invalid")
            }
            
        full_key = key.replace("thumbnail/", "image/", 1)
        full_url = f"https://{bucket_name}.s3.amazonaws.com/{full_key}"
        
        return {
            'statusCode': 200,
            'body': json.dumps({"full_image_url": full_url})
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"{str(e)}")
        }
