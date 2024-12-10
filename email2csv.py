import os
import json
import csv
from email import policy
from email.parser import BytesParser
from bs4 import BeautifulSoup
from tqdm import tqdm
from termcolor import cprint

def extract_email_info(file_path):
    """
    Extract information from an email file (.eml).

    Args:
        file_path (str): Path to the .eml file.

    Returns:
        dict: A dictionary containing extracted email information with keys:
            - Origin: Filename of the .eml file
            - Subject: Email subject
            - To: Recipient(s) of the email
            - From: Sender of the email
            - Cc: Carbon copy recipient(s)
            - Bcc: Blind carbon copy recipient(s)
            - Date: Date of the email
            - Attachment_Count: Number of attachments
            - Mail_Body: Plain text content of the email body
    """
    with open(file_path, "rb") as f:
        msg = BytesParser(policy=policy.default).parse(f)

    mail_body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                mail_body = part.get_payload(decode=True).decode()
                break
            elif part.get_content_type() == "text/html":
                html_content = part.get_payload(decode=True).decode()
                mail_body = BeautifulSoup(html_content, "html.parser").get_text()
                break
    else:
        if msg.get_content_type() == "text/plain":
            mail_body = msg.get_payload(decode=True).decode()
        elif msg.get_content_type() == "text/html":
            html_content = msg.get_payload(decode=True).decode()
            mail_body = BeautifulSoup(html_content, "html.parser").get_text()

    # Clean up the extracted text
    mail_body = " ".join(mail_body.split())  # Remove extra whitespace

    attachment_count = sum(
        1 for part in msg.walk() if part.get_content_disposition() == "attachment"
    )

    return {
        "Origin": os.path.basename(file_path),
        "Subject": msg.get("Subject", "No Subject Specified"),
        "To": msg.get("To", "No Recipients (Draft)"),
        "From": msg.get("From", "Error in Loading Origin"),
        "Cc": msg.get("Cc", ""),
        "Bcc": msg.get("Bcc", ""),
        "Date": msg.get("Date", "Error parsing Date"),
        "Attachment_Count": attachment_count,
        "Mail_Body": mail_body.strip(),
    }


def process_eml_files(directory):
    """
    Process all .eml files in a given directory.

    Args:
        directory (str): Path to the directory containing .eml files.

    Returns:
        list: A list of dictionaries, each containing information extracted from an .eml file.
    """
    email_data = []
    for idx, filename in enumerate(tqdm(os.listdir(directory))):
        if filename.endswith(".eml"):
            file_path = os.path.join(directory, filename)
            email_info = extract_email_info(file_path)
            email_data.append(email_info)
            cprint(f"PARSED: {file_path}", color="green")
        cprint(f"Total Files Parsed: {idx+1}", "yellow")
    return email_data


def save_as_json(data, output_file):
    """
    Save the extracted email data as a JSON file.

    Args:
        data (list): List of dictionaries containing email information.
        output_file (str): Path to the output JSON file.
    """
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def save_as_csv(data, output_file):
    """
    Save the extracted email data as a CSV file.

    Args:
        data (list): List of dictionaries containing email information.
        output_file (str): Path to the output CSV file.
    """
    keys = data[0].keys()
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)


if __name__ == "__main__":
    file_name = "set2_better"
    eml_directory = "./data/Simulation/Set 2/Original format/"
    email_data = process_eml_files(eml_directory)

    save_as_json(email_data, f"{file_name}.json")
    save_as_csv(email_data, f"{file_name}.csv")