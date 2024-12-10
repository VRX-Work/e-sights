import os
import glob
import pandas as pd
from termcolor import cprint
from email import policy
from email.parser import BytesParser
from tqdm import tqdm
import re


def generate_email_list(path: str, extension: str) -> list:
    mail_list = []
    for idx, file in enumerate(
        tqdm(glob.glob(os.path.join(path, f"*.{extension}")), leave=True)
    ):
        print(f"{idx+1}. Parsing {file}")
        with open(file, "rb") as eml_file:
            mail = BytesParser(policy=policy.default).parse(eml_file)
            mail_body = ""

            try:
                mail_body = mail.get_body(preferencelist=("plain")).get_content()
            except AttributeError:
                html_body = mail.get_body(preferencelist=("html"))
            if html_body:
                mail_body = re.sub(
                    r"\s+", " ", re.sub(r"<[^>]+>", "", str(html_body.get_content()))
                ).strip()
            else:
                mail_body = ""

            mail_dict = {
                "Subject": mail.get("Subject", "No Subject Specified"),
                "To": mail.get("To", "No Recipients (Draft)"),
                "From": mail.get("From", "Error in Loading Origin"),
                "Cc": mail.get("Cc", ""),
                "Bcc": mail.get("Bcc", ""),
                "Date": mail.get("Date", "Error parsing Date"),
                "Attachment_Count": mail.get("Attachment-Count", 0),
                "Mail_Body": mail_body,
            }

            mail_list.append(mail_dict)
            cprint(f"Parsed: {file}", "green", attrs=["bold"])

    print(f"Final List Size: {len(mail_list)}")
    return mail_list


def email_list2csv(email_list: list, file_name: str = "email_list.csv"):
    df = pd.DataFrame(email_list)
    df.to_csv(file_name)


if __name__ == "__main__":
    mails = generate_email_list(".\\data\\Simulation\\Set 1\\Original format\\", "eml")
    email_list2csv(mails)
