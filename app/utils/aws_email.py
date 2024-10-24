import boto3
from botocore.exceptions import ClientError

def send_verification_code_email(client, recipaint:str, verification_code:str):
    """
    Send a verification code to the user via email. 

    :param client: boto3 SES client
    :param recipaint: str, the email address of the recipient
    :param verification_code: str, the verification code to send to the user
    """ 

    print('Attempting to send verification code')
    # Email vars 
    sender = "your_ses_sender_email_here" # keeping our email private
    subject = "Your SN-AI Data App Verification Code"
    charset = 'UTF-8'

    # The HTML body of the email.
    body_html = f"""<html>
    <head></head>
    <body>
    <h1>Welcome to the Audience Insights Data App </h1>
    <p>This email was sent with
        <a href='https://aws.amazon.com/ses/'>Amazon SES</a> using the
        <a href='https://aws.amazon.com/sdk-for-python/'>
        AWS SDK for Python (Boto)</a>.</p>
        <br>
        <h2>Your verification code is: {verification_code}</h2>
    </body>
    </html>
                """      

    body_text = f"Your verification code is: {verification_code}"
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    recipaint,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': charset,
                        'Data': body_html,
                    },
                    'Text': {
                        'Charset': charset,
                        'Data': body_text,
                    },
                },
                'Subject': {
                    'Charset': charset,
                    'Data': subject,
                },
            },
            Source=sender,
            # If you are not using a configuration set, comment or delete the
            # following line
            #ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.	
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])


def send_password_reset_email(client:boto3.client, recipaint:str, link:str):
    """
    Send a verification code to the user via email. 

    :param client: boto3 SES client
    :param recipaint: str, the email address of the recipient
    :param link: str, the link to send to the user, relies on the frontend URL being set in the .env file
    """ 

    print('Attempting to send verification code')
    # Email vars 
    sender = "your_ses_sender_email_here" # keeping our email private
    subject = "Reset Your Password for the SN-AI Data App"
    charset = 'UTF-8'

    # The HTML body of the email.
    body_html = f"""<html>
    <head></head>
    <body>
        <h3>Please follow the link below to reset your password:</h3>
        <p style="margin-left: 10px;"><a href={link}>{link}</a></p>
        <p>Do not share this link with anyone!</p>
        <p>If you did not request a password reset, please ignore this email.</p>
        <br>
        <p>This email was sent with <a href='https://aws.amazon.com/ses/'> Amazon SES</a> 
        using the <a href='https://aws.amazon.com/sdk-for-python/'> AWS SDK for Python</a>.
        </p>

    </body>
    </html>
                """      
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    recipaint,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': charset,
                        'Data': body_html,
                    },
              
                },
                'Subject': {
                    'Charset': charset,
                    'Data': subject,
                },
            },
            Source=sender,
            # If you are not using a configuration set, comment or delete the
            # following line
            #ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.	
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])




