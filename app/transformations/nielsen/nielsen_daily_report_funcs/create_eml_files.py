import os

# Email Utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate
from datetime import datetime

def create_nielsen_daily_emails(dmalists:list, user_email:str, daily_date:str,
                                email_subjects:list, email_notes:list, email_recipients:list,  
                                dma_html_dict:dict, chart_path_dict:dict, table_path_dict:dict,
                                eml_dump_path:str):
    
    # Grab the day of the week
    day_of_week = datetime.strptime(daily_date,'%m/%d/%Y').strftime('%A')
    
    eml_file_paths = []
    
    # Loop through each email, in the original case, this is 2 emails
    for email_num in range(len(email_subjects)): 

        # Initialize the email variables
        email_subject_line = email_subjects[email_num]
        email_note = email_notes[email_num]
        email_dmas = dmalists[email_num]
        
        # Create the name of the email with the date and day of the week
        email_subject_full = str(email_subject_line) + ' - ' + str(day_of_week) +' ' + str(daily_date)

        # Create the email message, initialize the email
        msg = MIMEMultipart()
        msg['From'] = user_email
        msg['To'] = ", ".join(email_recipients[email_num])
        msg['Subject'] = email_subject_full
        msg['Date'] = formatdate(localtime=True)

        # Add each html body to the email
        body_html = ''
        for dma in email_dmas:
            body_html += dma_html_dict[dma]
        final_email_html =  email_note + '<hr color="black" size="2" width="100%">' + body_html
        msg.attach(MIMEText(final_email_html, 'html'))

        # Attach each graph to the email
        for image_path, content_id in chart_path_dict.items():
            content_id_stripped = content_id.replace('<','').replace('>','')
            if content_id_stripped in final_email_html:
                with open(image_path, 'rb') as img_file:
                    img = MIMEImage(img_file.read())
                    img.add_header('Content-ID', content_id)
                    img.add_header('Content-Disposition', 'inline', filename=os.path.basename(image_path))
                    msg.attach(img)

        # Add each table to the email
        for image_path, content_id in table_path_dict.items():
            content_id_stripped = content_id.replace('<','').replace('>','')
            if content_id_stripped in final_email_html:
                with open(image_path, 'rb') as img_file:
                    img = MIMEImage(img_file.read())
                    img.add_header('Content-ID', content_id)
                    img.add_header('Content-Disposition', 'inline', filename=os.path.basename(image_path))
                    msg.attach(img)
                
        # Write the email to a .eml file
        email_file_name = str(email_subject_line) + '_' + (str(daily_date).replace('/','-')) + '.eml'
        eml_file_path = os.path.join(eml_dump_path, email_file_name)
        with open(eml_file_path, "w") as eml_file:
            eml_file.write(msg.as_string())

        eml_file_paths.append(eml_file_path)

    return eml_file_paths
