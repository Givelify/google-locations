"""Long running script used to test SNS publish locally"""

import time

import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Config
LOCALSTACK_ENDPOINT = "http://localhost:4566"
REGION = "us-east-1"

# Already created topic and queue
TOPIC_ARN = "arn:aws:sns:us-east-1:000000000000:my-topic.fifo"
QUEUE_URL = "http://localhost:4566/000000000000/my-queue"

# Dummy credentials for LocalStack
AWS_ACCESS_KEY = "test"
AWS_SECRET_KEY = "test"

# Create clients with dummy credentials
sns = boto3.client(
    "sns",
    endpoint_url=LOCALSTACK_ENDPOINT,
    region_name=REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
)

sqs = boto3.client(
    "sqs",
    endpoint_url=LOCALSTACK_ENDPOINT,
    region_name=REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
)

# Publish a test message
MESSAGE = "Hello LocalStack! Testing SNS -> SQS FIFO"
sns.publish(
    TopicArn=TOPIC_ARN,
    Message=MESSAGE,
    MessageGroupId="default",
    MessageDeduplicationId="unique-id-1234",
)
print(f"Published message to SNS topic: {MESSAGE}")

# Continuously poll SQS
print("Listening for messages on SQS...")

while True:
    try:
        response = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10,
        )

        messages = response.get("Messages", [])
        if messages:
            for msg in messages:
                print(f"Message received from SQS: {msg['Body']}")
                sqs.delete_message(
                    QueueUrl=QUEUE_URL, ReceiptHandle=msg["ReceiptHandle"]
                )
        else:
            time.sleep(0.5)

    except (BotoCoreError, ClientError) as e:
        print(f"Error receiving messages: {e}")
        time.sleep(5)
