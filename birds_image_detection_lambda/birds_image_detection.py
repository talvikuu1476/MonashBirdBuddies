from ultralytics import YOLO
import supervision as sv
import cv2 as cv
import boto3
import os
from collections import Counter

def image_prediction(image_path, confidence=0.5, model="./model.pt"):
    """
    Function to display predictions of a pre-trained YOLO model on a given image.

    Parameters:
        image_path (str): Path to the image file. Can be a local path or a URL.
        result_path (str): If not None, this is the output filename.
        confidence (float): 0-1, only results over this value are saved.
        model (str): path to the model.
    """

    # Load YOLO model
    model = YOLO(model)
    class_dict = model.names

    # Load image from local path
    img = cv.imread(image_path)

    # Check if image was loaded successfully
    if img is None:
        print("Couldn't load the image! Please check the image path.")
        return

    result = model(img)[0]

    # Convert YOLO result to Detections format
    detections = sv.Detections.from_ultralytics(result)

    # Filter detections based on confidence threshold and check if any exist
    if detections.class_id is not None:
        detections = detections[(detections.confidence > confidence)]

        # Create labels for the detected objects
        labels = [f"{class_dict[cls_id]}" for cls_id in 
                  detections.class_id]
        return labels
    return []

s3_client = boto3.client('s3')
def handler(event, context):
    """
    AWS Lambda handler function to process S3 events and perform video detection using a YOLO model.
    This function is triggered when a new video file is uploaded to an S3 bucket.
    Parameters:
        event (dict): The event data containing information about the S3 bucket and object.
        context (object): The context object containing runtime information.
    """
    
    # initialise s3 and DynamoDB
    s3_client = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')
    table_name = "recognized_results" #
    
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        
        # download the video from s3
        local_image_path = f"/tmp/{key.split('/')[-1]}"
        s3_client.download_file(bucket, key, local_image_path)
        # Generate thumbnail from the downloaded image
        output = create_thumbnail(local_image_path)

        upload_thumbnail_to_s3(bucket,key,output)
        labels = image_prediction(local_image_path)
        counts = Counter(labels)
        # Create an SNS client
        sns_client = boto3.client('sns')
        
        ### Publish a notification to SNS
        publish_tag_notifications(sns_client,"https://{0}.s3.us-east-1.amazonaws.com/{1}".format(bucket,key),counts,"arn:aws:sns:us-east-1:260365280007:Notification")
        
        # save the labels to DynamoDB
        try:
            dynamodb.Table(table_name).put_item(
                Item={
                    'id': key,
                    'bucket': bucket,
                    'labels': counts
                }
            )
        except Exception as e:
            print(f"Error saving to DynamoDB: {e}")


def create_thumbnail(image_path: str, width: int = 150, height: int = 150) -> bytes | None:
    """
    Generates a thumbnail of the specified image.

    Args:
        image_path (str): Absolute or relative path to the image file.
        width (int): Target thumbnail width.
        height (int): Target thumbnail height.

    Returns:
        bytes | None: Encoded thumbnail image in bytes, or None if processing fails.
    """
    _, ext = os.path.splitext(image_path)
    img = cv.imread(image_path)

    if img is None:
        return None  # Image could not be loaded

    try:
        thumbnail = cv.resize(img, (width, height), interpolation=cv.INTER_AREA)
        success, buffer = cv.imencode(ext, thumbnail)
        return buffer.tobytes() if success else None
    except Exception as e:
        # Optional: log error
        return None




def upload_thumbnail_to_s3(bucket_name: str, original_key: str, thumbnail_bytes: bytes):
    """
    Upload the thumbnail image to S3 under 'thumbnail/' prefix.

    Args:
        bucket_name (str): Name of the S3 bucket.
        original_key (str): Original file key in S3 (e.g., 'uploads/image1.jpg').
        thumbnail_bytes (bytes): Thumbnail image content.
    """
    filename = os.path.basename(original_key)
    thumbnail_key = f"thumbnail/{filename}"

    s3_client.put_object(
        Bucket=bucket_name,
        Key=thumbnail_key,
        Body=thumbnail_bytes
    )

    return thumbnail_key

# sns function
def publish_tag_notifications(sns_client, s3_url: str, tag_counts: dict, topic_arn: str):
    """
    Publish SNS messages for each detected bird tag, including count info.

    Args:
        sns_client: boto3 SNS client
        s3_url (str): S3 URL of the uploaded image
        tag_counts (dict): Dictionary like {"crow": 2, "sparrow": 1}
        topic_arn (str): ARN of the SNS topic
    """
    for tag, count in tag_counts.items():
        message = (
            f"A new image was uploaded to the system.\n"
            f"S3 URL: {s3_url}\n"
            f"Detected bird species: {tag} (count: {count})"
        )

        try:
            response = sns_client.publish(
                TopicArn=topic_arn,
                Message=message,
                Subject='[BirdTag] New Bird Image Uploaded',
                MessageAttributes={
                    'tag': {
                        'DataType': 'String',
                        'StringValue': tag
                    },
                    'count': {
                        'DataType': 'Number',
                        'StringValue': str(count)
                    }
                }
            )
            print(f"SNS notification sent for tag '{tag}': {response['MessageId']}")
        except Exception as e:
            print(f"[Error] Failed to send SNS for tag '{tag}': {str(e)}")
