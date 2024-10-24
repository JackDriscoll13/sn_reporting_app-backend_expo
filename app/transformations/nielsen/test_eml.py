# Standard Libs
import smtplib
import os

# Email Utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate

def create_eml_download_email_test(to_email: str):
    """
    Send an email with an optional attachment.
    """
    current_dir = os.getcwd()
    # print(f"Current directory: {current_dir}")
    # print("Directory contents:")
    # for item in os.listdir(current_dir):
    #     print(item)

    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = 'jack.driscoll@charter.com'
    msg['To'] = to_email
    msg["Subject"] = "Email Report with Graphs"
    msg["Date"] = formatdate(localtime=True)
    
     # HTML email body with reference to image attachments
    html = """
    <html>
    <body>
        <h1>Your Report</h1>
        <p>Attached are the graphs for your report.</p>
        <img src="cid:graph1">
        <img src="cid:graph2">
    </body>
    </html>
    """

    msg.attach(MIMEText(html, "html"))


    # Attach graphs as inline images
    with open("resources/nielsendump/test0.png", "rb") as f1, open("resources/nielsendump/test1.png", "rb") as f2:
        img1 = MIMEImage(f1.read())
        img2 = MIMEImage(f2.read())

        # Set content-id for inline embedding
        img1.add_header("Content-ID", "<graph1>")
        img2.add_header("Content-ID", "<graph2>")

        msg.attach(img1)
        msg.attach(img2)

    # Write the email to a .eml file
    eml_file_path = "resources/nielsendump/email_report.eml"
    with open(eml_file_path, "w") as eml_file:
        eml_file.write(msg.as_string())

    print("EML file created at: ", eml_file_path)
    return eml_file_path
    