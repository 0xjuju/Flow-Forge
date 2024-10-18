from celery import shared_task
from django.test import TestCase
from moto import mock_aws
import boto3
from decouple import config


@shared_task
def add(x, y):
    return x + y


class TestAWSTasks(TestCase):
    def setUp(self):
        pass

    def test_add_task(self):
        # Test the Celery task
        result = add.apply(args=(3, 5))
        assert result.status == 'SUCCESS'
        assert result.result == 8

    @mock_aws
    def test_sqs_message_received(self):
        # Mock the SQS queue using mock_aws from moto
        access_key = config('AWS_ACCESS_KEY_ID', default='fake_access_key')
        secret_key = config('AWS_SECRET_ACCESS_KEY', default='fake_secret_key')
        region = config('AWS_REGION', default='us-east-1')
        queue_name = config('SQS_QUEUE_NAME', default='test_queue')

        # Create a mocked SQS queue
        sqs = boto3.client('sqs', region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        queue = sqs.create_queue(QueueName=queue_name)
        queue_url = queue['QueueUrl']

        # Send a test message to SQS
        sqs.send_message(QueueUrl=queue_url, MessageBody='{"test_key": "test_value"}')

        # Receive the message from SQS
        response = sqs.receive_message(QueueUrl=queue_url)
        messages = response.get('Messages', [])

        assert len(messages) > 0
        assert messages[0]['Body'] == '{"test_key": "test_value"}'
