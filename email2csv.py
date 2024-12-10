import os
import glob
import pandas as pd
from termcolor import cprint
from email import policy
from email.parser import BytesParser
from tqdm import tqdm
import re


def generate_email_list(path: str, extension: str) -> list:
    """Generates a list of email details from .eml files in a specified directory.

    This function scans a given directory for files with a specified extension,
    parses each email file to extract relevant information such as subject, sender,
    recipients, date, and the body of the email. It handles both plain text and HTML
    email formats.

    Args:
        path (str): The directory path where the .eml files are located.
        extension (str): The file extension of the email files to be processed (e.g., 'eml').

    Returns:
        list: A list of dictionaries, each containing details of an email. Each dictionary
              includes keys such as 'Subject', 'To', 'From', 'Cc', 'Bcc', 'Date',
              'Attachment_Count', and 'Mail_Body'.
    """
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
                "Origin": os.path.basename(file),
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


def email_list2csv(email_list: list, file_name: str = "email_list.csv") -> None:
    """Saves a list of email details to a CSV file.

    This function takes a list of email dictionaries and converts it into a Pandas DataFrame,
    then saves the DataFrame to a specified CSV file. Each dictionary in the list should
    represent an email with relevant fields such as subject, sender, recipients, and body.

    Args:
        email_list (list): A list of dictionaries containing email details. Each dictionary
                           should include keys like 'Subject', 'To', 'From', 'Cc', 'Bcc',
                           'Date', 'Attachment_Count', and 'Mail_Body'.
        file_name (str, optional): The name of the output CSV file. Defaults to "email_list.csv".

    Returns:
        None: This function does not return any value; it directly saves the CSV file.
    """
    df = pd.DataFrame(email_list)
    df.to_csv(file_name)


if __name__ == "__main__":
    mails = generate_email_list(".\\data\\Simulation\\Set 1\\Original format\\", "eml")
    email_list2csv(mails, "set_1_parsed.csv")
