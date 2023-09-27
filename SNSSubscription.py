import boto3
import logging

def lambda_handler(event, context):
    # Set the log level based on the environment variable LOG_LEVEL
    LOG_LEVEL = os.getenv('LOG_LEVEL')
    logging.getLogger().setLevel(LOG_LEVEL)

    try:
        logging.info('Event Data: ')
        logging.info(event)
        
        # Define the ARN of the Control Tower SNS topic in the audit account
        sns_topic_arn = 'arn:aws:sns:us-east-1:866232342806:aws-controltower-AllConfigNotifications'
        
        # Check if the event has a 'source' field
        if 'source' in event:
            event_source = event['source']
            logging.info(f'Control Tower Event Source: {event_source}')
            event_name = event['detail']['eventName']
            logging.info(f'Control Tower Event Name: {event_name}')
            
            # Check if the event source is Control Tower and the event name is relevant
            if event_source == 'aws.controltower' and event_name in ['UpdateManagedAccount', 'CreateManagedAccount', 'UpdateLandingZone']:
                # Add an SNS subscription to the audit account's topic
                add_sns_subscription(sns_topic_arn)
                
        logging.info('Execution Successful')
        
        # TODO implement
        return {
            'statusCode': 200
        }

    except Exception as e:
        exception_type = e.__class__.__name__
        exception_message = str(e)
        logging.exception(f'{exception_type}: {exception_message}')

def add_sns_subscription(topic_arn):
    # Create an SNS client
    sns_client = boto3.client('sns')
    
    # Define the ARN of the PROD-Security-10021 SQS queue
    sqs_arn = 'arn:aws:sqs:us-east-1:234324814398:aws-config-to-snow-queue'
    
    try:
        # Create a PROD-Security-10021 SNS subscription to the specified SQS queue
        response = sns_client.subscribe(
            TopicArn=topic_arn,
            Protocol='sqs',
            Endpoint=sqs_arn
        )
        
        logging.info(f'Subscription request sent to {topic_arn}')
    
    except Exception as e:
        exception_type = e.__class__.__name__
        exception_message = str(e)
        logging.exception(f'Error adding SNS subscription: {exception_type}: {exception_message}')

