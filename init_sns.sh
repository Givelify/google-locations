#!/bin/bash
set -e

# Create SNS topic
TOPIC_ARN=$(awslocal sns create-topic \
    --name my-topic.fifo \
    --attributes FifoTopic=true \
    --query 'TopicArn' --output text)
echo "Created FIFO SNS topic: $TOPIC_ARN"

# Create SQS queue
QUEUE_URL=$(awslocal sqs create-queue --queue-name my-queue --query 'QueueUrl' --output text)
echo "Created SQS queue: $QUEUE_URL"

# Get SQS ARN
QUEUE_ARN=$(awslocal sqs get-queue-attributes \
  --queue-url $QUEUE_URL \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' \
  --output text)
echo "SQS ARN: $QUEUE_ARN"

# Subscribe SQS to SNS
awslocal sns subscribe \
  --topic-arn $TOPIC_ARN \
  --protocol sqs \
  --notification-endpoint $QUEUE_ARN
echo "Subscribed SQS to SNS"
