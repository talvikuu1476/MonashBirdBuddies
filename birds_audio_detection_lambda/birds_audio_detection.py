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


# 初始化 AWS 客户端
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get("TABLE_NAME", "recognized_results")
table = dynamodb.Table(table_name)
def lambda_handler(event, context):
    save_model()
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(record['s3']['object']['key'])

        
        filename = key.split('/')[-1]
        local_path = f"/tmp/{filename}"

        try:
            # 下载音频文件
            s3.download_file(bucket, key, local_path)
            print(f"Downloaded: {local_path}")

            # audio = AudioSegment.from_file(local_path)
            # mono_audio = audio.set_channels(1)
            # # Overwrite the same file with mono version
            # ext = Path(local_path).suffix.lstrip(".").lower()
            # mono_audio.export(local_path, format=ext)
            # print("successfully exported the mono audio")
            # 模拟音频识别标签
            tags = simulate_audio_tags(local_path)
            tags = Counter(tags)
            print(tags)

            # 存入 DynamoDB
            table.put_item(Item={
                "id": key,
                "bucket": bucket,
                "labels": tags
            })
            print(f"Saved tags: {tags}")
        except Exception as e:
            print(f"Error: {e}")

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
    # 这里可以换成实际音频识别逻辑
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