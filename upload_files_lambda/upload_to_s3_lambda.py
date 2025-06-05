# upload_to_s3_lambda.py
import boto3
import base64
import os

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get("BUCKET_NAME", "MonashBirdBuddies-S3")

def lambda_handler(event, context):
    file_content = base64.b64decode(event["file_data"])
    file_name = event["file_name"]

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=file_name,
        Body=file_content,
        ContentType='image/jpeg'
    )

    return {
        'statusCode': 200,
        'body': f"Uploaded {file_name} to {BUCKET_NAME}."
    }

# ///
# 传 upload_files_lambda.zip 到某个 bucket：
# cd upload_files_lambda
# zip upload_files_lambda.zip upload_to_s3_lambda.py
# aws s3 cp upload_files_lambda.zip s3://MonashBirdBuddies-S3/
# ///