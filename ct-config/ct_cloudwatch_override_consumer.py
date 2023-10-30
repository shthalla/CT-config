import boto3
import json
import logging
import botocore.exceptions
import os

def lambda_handler(event, context):

    LOG_LEVEL = os.getenv('LOG_LEVEL')
    logging.getLogger().setLevel(LOG_LEVEL)

    try:

        logging.info('Event Body:')

        body = json.loads(event['Records'][0]['body'])
        account_id = body['Account']
        aws_region = body['Region']
        event = body['Event']

        logging.info(f'Extracted Account: {account_id}')
        logging.info(f'Extracted Region: {aws_region}')
        logging.info(f'Extracted Event: {event}')

        bc = botocore.__version__
        b3 = boto3.__version__

        logging.info(f'Botocore : {bc}')
        logging.info(f'Boto3 : {b3}')

        STS = boto3.client("sts")

        def assume_role(account_id, role='AWSControlTowerExecution'):
            '''
            Return a session in the target account using Control Tower Role
            '''
            try:
                curr_account = STS.get_caller_identity()['Account']
                if curr_account != account_id:
                    part = STS.get_caller_identity()['Arn'].split(":")[1]

                    role_arn = 'arn:' + part + ':iam::' + account_id + ':role/' + role
                    ses_name = str(account_id + '-' + role)
                    response = STS.assume_role(RoleArn=role_arn, RoleSessionName=ses_name)
                    sts_session = boto3.Session(
                        aws_access_key_id=response['Credentials']['AccessKeyId'],
                        aws_secret_access_key=response['Credentials']['SecretAccessKey'],
                        aws_session_token=response['Credentials']['SessionToken'])

                    return sts_session
            except botocore.exceptions.ClientError as exe:
                logging.error('Unable to assume role')
                raise exe

        sts_session = assume_role(account_id)
        logging.info(f'Printing STS session: {sts_session}')

        # Use the session and create a client for lambda
        lambda_client = sts_session.client('lambda', region_name=aws_region)

        # ControlTower created lambda with name "aws-controltower-NotificationForwarder" and we will update just that

        function_name = 'aws-controltower-NotificationForwarder'
        function_arn = f"arn:aws:lambda:{aws_region}:{account_id}:function:{function_name}"

        tags = {
            'POC': 'cloudops-platform@ellucian.com',
            'Service': 'controltower-lambda'
        }

        try:
            # Check if the Lambda function exists before adding tags
            lambda_client.get_function(FunctionName=function_name)

            role_arn = 'arn:aws:iam::' + account_id + ':role/aws-controltower-ForwardSnsNotificationRole'

            # Add tags to the Lambda function
            lambda_client.tag_resource(
                Resource=function_arn,
                Tags=tags
            )
            logging.info(f'Tags added to Lambda function {function_name}: {tags}')

        except lambda_client.exceptions.ResourceNotFoundException as e:
            logging.warning(f'Lambda function {function_name} not found. Moving to the next queue.')

        except Exception as e:
            logging.error(f'Error adding tags to Lambda function {function_name}: {str(e)}')

        return {
            'statusCode': 200
        }

    except Exception as e:
        exception_type = e.__class__.__name__
        exception_message = str(e)
        logging.exception(f'{exception_type}: {exception_message}')
