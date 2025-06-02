aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 260365280007.dkr.ecr.us-east-1.amazonaws.com

docker build -t birds_detection_image .

docker tag birds_detection_image:latest 260365280007.dkr.ecr.us-east-1.amazonaws.com/birds_detection_image:latest

docker push 260365280007.dkr.ecr.us-east-1.amazonaws.com/birds_detection_image:latest

aws lambda create-function \
  --function-name image_detection \
  --package-type Image \
  --code ImageUri=260365280007.dkr.ecr.us-east-1.amazonaws.com/birds_detection_image:latest \
  --role arn:aws:iam::260365280007:role/LabRole \
  --architectures arm64 \
  --region us-east-1

aws lambda update-function-code \
  --function-name image_detection \
  --image-uri 260365280007.dkr.ecr.us-east-1.amazonaws.com/birds_detection_image:latest \
  --region us-east-1 \
  --publish