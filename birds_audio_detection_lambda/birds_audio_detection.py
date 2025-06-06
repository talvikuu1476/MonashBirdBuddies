import boto3
import os
import urllib.parse
import logging
from collections import Counter
from urllib.parse import unquote_plus
import logging
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer
from pathlib import Path


s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get("TABLE_NAME", "recognized_results")
table = dynamodb.Table(table_name)
def lambda_handler(event, context):
    save_model()
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key    = urllib.parse.unquote_plus(record['s3']['object']['key'])
        filename = key.split('/')[-1]
        local_path = f"/tmp/{filename}"

        try:
            s3.download_file(bucket, key, local_path)
            print("Downloaded:", local_path)

            raw_tags = simulate_audio_tags(local_path)
            tags_cap = [t.capitalize() for t in raw_tags]
            counts   = Counter(tags_cap)
            print("Counts:", counts)

            sns_client = boto3.client('sns')
            s3_url     = f"https://{bucket}.s3.us-east-1.amazonaws.com/{key}"
            publish_tag_notifications(
                sns_client,
                s3_url,
                counts,
                "arn:aws:sns:us-east-1:260365280007:Notification"
            )

            table.put_item(Item={
                "id": key,
                "bucket": bucket,
                "labels": counts
            })

        except Exception as e:
            print("Error:", e)

    return {"statusCode": 200, "body": "Processed audio file."}


def save_model():
    logger = logging.getLogger()
    if not os.path.isfile('/tmp/BirdNET_GLOBAL_6K_V2.4_Labels.txt'):
        logger.info("downloading BirdNET_GLOBAL_6K_V2.4_Labels.txt from S3")
        s3.download_file("team163-bucket",'Models/BirdNET_GLOBAL_6K_V2.4_Labels.txt','/tmp/BirdNET_GLOBAL_6K_V2.4_Labels.txt')
    else:
        logger.info("BirdNET_GLOBAL_6K_V2.4_Labels.txt exsits")

    if not os.path.isfile('/tmp/BirdNET_GLOBAL_6K_V2.4.tflite'):
        logger.info("downloading BirdNET_GLOBAL_6K_V2.4.tflite from S3")
        s3.download_file("team163-bucket",'Models/BirdNET_GLOBAL_6K_V2.4.tflite','/tmp/BirdNET_GLOBAL_6K_V2.4.tflite')
    else:
        logger.info("BirdNET_GLOBAL_6K_V2.4.tflite exsits")

def simulate_audio_tags(audio_path,threshold=0.3):

    MODEL_PATH = os.path.join(
        "/tmp/BirdNET_GLOBAL_6K_V2.4.tflite",
    )
    LABEL_PATH = os.path.join(
        "/tmp/BirdNET_GLOBAL_6K_V2.4_Labels.txt"
    )

    analyzer = Analyzer(
        classifier_model_path=MODEL_PATH,
        classifier_labels_path=LABEL_PATH,
    )

    recording = Recording(
        analyzer,
        audio_path,
        min_conf=threshold,
    )
    recording.analyze()
    labels = []
    for detection in recording.detections:
        labels.append(detection["common_name"])

    return labels

if __name__ == "__main__":
    # from pydub import AudioSegment
    # audio = AudioSegment.from_file("birds_singing_in_garden.wav")
    # mono_audio = audio.set_channels(1)
    # mono_audio.export("birds_mono.wav", format="wav")
    species = simulate_audio_tags("birds_mono.wav")
    print(species)


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
                Subject='[BirdTag] New Bird Audio Uploaded',
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