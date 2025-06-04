#创建镜像
aws ecr create-repository --repository-name audio_detection --region us-east-1 --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE

aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 260365280007.dkr.ecr.us-east-1.amazonaws.com

docker build -t audio_detection .

docker tag audio_detection:latest 260365280007.dkr.ecr.us-east-1.amazonaws.com/audio_detection:latest

docker push 260365280007.dkr.ecr.us-east-1.amazonaws.com/audio_detection:latest

<!-- create lambda function -->
aws lambda create-function \
  --function-name audio_detection \
  --package-type Image \
  --code ImageUri=260365280007.dkr.ecr.us-east-1.amazonaws.com/audio_detection:latest \
  --role arn:aws:iam::260365280007:role/LabRole \
  --region us-east-1 \
  --architecture arm64

aws lambda update-function-code \
--function-name audio_detection \
--image-uri 260365280007.dkr.ecr.us-east-1.amazonaws.com/audio_detection:latest \
--region us-east-1 \
--publish