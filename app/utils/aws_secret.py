import boto3
from botocore.exceptions import ClientError

# If we start using secrets manager we can use a function loike this to retreive screts
# Note that we will need to configure our AWS cli or IAM roles to instance(if deployed on EC2) to have access to the secrets manager
def get_secret(secret_name, region_name="us-east-2"):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise e
    else:
        if 'SecretString' in get_secret_value_response:
            return get_secret_value_response['SecretString']
        else:
            return get_secret_value_response['SecretBinary']
        
