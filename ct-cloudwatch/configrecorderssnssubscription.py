#lambda to add subscription of SQS to the config recorders SNS Topic in the Audit account

import json
import boto3

def lambda_handler(event, context):

    sns_client = boto3.client('sns')
    
    target_topic_arn = 'arn:aws:sns:us-east-1:866232342806:aws-controltower-AllConfigNotifications'
    
    sqs_arn = 'arn:aws:sqs:us-east-1:234324814398:aws-config-to-snow-queue'
    
    try:
        # Extract relevant information from the CloudTrail event
        event_detail = event['detail']
        event_name = event_detail['eventName']
        request_parameters = event_detail.get('requestParameters', {})
        topic_arn = request_parameters.get('topicArn', '')
        
        # Check if the event is related to changing SNS topic attributes
        if (
            event_name == 'SetTopicAttributes'
            and topic_arn == target_topic_arn
        ):
            # Log the event
            print(f"Received CloudTrail event for SNS topic attribute change: {event_name}")
            
            # Check if the subscription already exists for the SQS queue
            existing_subscriptions = sns_client.list_subscriptions_by_topic(TopicArn=target_topic_arn)
            for subscription in existing_subscriptions.get('Subscriptions', []):
                if subscription['Protocol'] == 'sqs' and subscription['Endpoint'] == sqs_arn:
                    print("Subscription already exists. No action needed.")
                    return
            
            # Subscription doesn't exist; add a subscription to the SNS topic for the specified SQS queue
            response = sns_client.subscribe(
                TopicArn=target_topic_arn,
                Protocol='sqs',
                Endpoint=sqs_arn
            )
            
            print(f"Subscription response: {response}")
        
        else:
            # Event is not related to the target SNS topic, no action needed
            print(f"Ignored CloudTrail event: {event_name}")
    
    except Exception as e:
        # Handle any errors or exceptions
        print(f"Error processing CloudTrail event: {str(e)}")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Lambda function execution completed')
    }
    