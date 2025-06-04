#!/usr/bin/env python
# coding: utf-8

# requirements
# !pip install ultralytics supervision

from ultralytics import YOLO
from collections import Counter
import supervision as sv
import cv2 as cv
import boto3
import os
# fix "multiple copies of the OpenMP runtime have been linked into the program" issue
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# detect if a video has uploaded to s3
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
    table_name = "recognized_results"
    
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        
        # download the video from s3
        local_video_path = f"/tmp/{key.split('/')[-1]}"
        s3_client.download_file(bucket, key, local_video_path)
        
        labels = video_prediction(local_video_path, result_filename=key.split('/')[-1], confidence=0.5, model="./model.pt")
        counts = Counter(labels) # count each label
        
        # Create an SNS client
        sns_client = boto3.client('sns')
        
        # Publish a notification to SNS
        publish_tag_notifications(sns_client,
                                  "https://{0}.s3.us-east-1.amazonaws.com/{1}".format(bucket,key),
                                  counts,
                                  "arn:aws:sns:us-east-1:260365280007:Notification")

        # save the labels to DynamoDB
        try:
            dynamodb.Table(table_name).put_item(
                Item={
                    'id': key.split('/')[-1],
                    'bucket': bucket,
                    'labels': counts
                }
            )
        except Exception as e:
            print(f"Error saving to DynamoDB: {e}")
       
       
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

# Video Detection
def video_prediction(video_path, result_filename=None, confidence=0.5, model="./model.pt"):
    """
    Function to make predictions on video frames using a trained YOLO model and display the video with annotations.

    Parameters:
        video_path (str): Path to the video file.
        save_video (bool): If True, saves the video with annotations. Default is False.
        filename (str): The name of the output file where the video will be saved if save_video is True.
    """
    
    # initialise a list storing labels
    labels = []
    
    try:
        # Load video info and extract width, height, and frames per second (fps)
        video_info = sv.VideoInfo.from_video_path(video_path=video_path)
        fps = int(video_info.fps)

        # Initialize YOLO model and tracker
        model = YOLO(model)  # Load your custom-trained YOLO model
        tracker = sv.ByteTrack(frame_rate=fps)  # Initialize the tracker with the video's frame rate
        class_dict = model.names  # Get the class labels from the model

        # Capture the video from the given path
        cap = cv.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception("Error: couldn't open the video!")

        # Process the video frame by frame
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:  # End of the video
                break

            # Make predictions on the current frame using the YOLO model
            result = model(frame)[0]
            detections = sv.Detections.from_ultralytics(result)  # Convert model output to Detections format
            detections = tracker.update_with_detections(detections=detections)  # Track detected objects

            # Filter detections based on confidence
            if detections.tracker_id is not None:
                detections = detections[(detections.confidence > confidence)]  # Keep detections with confidence greater than a threashold

                # Generate labels for tracked objects
                label = [f"{class_dict[cls_id]}" for cls_id in detections.class_id]
                labels.extend(label)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Release resources
        cap.release()
        print("Video processing complete, Released resources.")

    return labels

