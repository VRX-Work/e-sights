import os
import glob
import json
import pandas as pd
from termcolor import cprint
from EMLMailReader import MailReader, RxMailMessage

from tqdm import tqdm
import re


def generate_email_list(path: str, extension: str) -> list:
    reader = MailReader()
    mail_list = []
    for file in tqdm(glob.glob(os.path.join(path, f"*.{extension}")), leave=True):
        print(f"Parsing {file}")
        raw_email = reader.get_email(file)

        if isinstance(raw_email, RxMailMessage):
            mail_string = raw_email.export_as_json()
            mail = json.loads(mail_string)

            try:
                mail_body = parse_mail_html(raw_email.Body)
            
            except AttributeError:
                mail_body = ""
                print(f"No Body in {file}")

            mail_dict = {
                "Subject": mail.get("Subject", "No Subject Specified"),
                "To": mail.get("To", "No Recipients (Draft)"),
                "From": mail.get("From", "Error in Loading Origin"),
                "Cc": mail.get("Cc", "No mentions in CC"),
                "Bcc": mail.get("Bcc", "No mentions in BCC"),
                "Date": mail.get("Date", "Error parsing Date"),
                "Reply_To": mail.get("Reply-To", ""),
                "Attachment_Count": mail.get("Attachment-Count", 0),
                "Mail_Body": mail_body,
            }

            mail_list.append(mail_dict)
            cprint(f"Parsed: {file}", "green", attrs=['bold'])
        else:
            cprint(f"Failed: {file}", "red", attrs=['bold'])
    
    print(f"Final List Size: {len(mail_list)}")
    return mail_list


def parse_mail_html(mail_html: str) -> str:
    body = re.sub(r'\s+', ' ', re.sub( r"<[^>]+>", "", str(mail_html))).strip()
    return body


def email_list2csv(email_list: list):
    pass


if __name__ == "__main__":
    print(generate_email_list(".\\data\\Simulation\\Set 1\\Original format\\", "eml"))
