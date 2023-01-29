"""Import smtp library for sending Office 365 email."""
import mimetypes
import smtplib
import time
from datetime import date
from email.headerregistry import Address
from email.message import EmailMessage

from retrying import retry


@retry(stop_max_attempt_number=2, wait_fixed=2000, stop_max_delay=10000)
def office365_connection(o365_username, o365_password, message):
    """Connects to Office 365 SMTP server
       and retires up to 2 times."""
    with smtplib.SMTP("smtp.office365.com", 587) as smtpserver:
        smtpserver.ehlo()
        smtpserver.starttls()
        smtpserver.login(o365_username, o365_password)
        smtpserver.send_message(message)
        print(f'{date.today()} {time.strftime("%H:%M:%S")}')


def add_attachment(message, filename, content_id):
    """Add attachment to message"""
    with open(filename, "rb") as img:

        # know the Content-Type of the image
        maintype, subtype = mimetypes.guess_type(img.name)[0].split("/")

        # attach it
        message.get_payload()[1].add_related(
            img.read(), maintype=maintype, subtype=subtype, cid=content_id
        )
    return message


def o365_send_email(
    o365_username,
    o365_password,
    recipient_email,
    subject_text,
    plain_text_body,
    html_body=None,
    email_cc=None,
    email_bcc=None,
    venue_image=None,
    venue_image_cid=None,
    company_image_cid=None,
):
    """Create and send an email message
    Print the time and date
    """

    message = EmailMessage()

    if ";" in recipient_email:
        message["To"] = recipient_email.split(";")
    else:
        message["To"] = recipient_email
    message["From"] = Address(display_name="reports", addr_spec=o365_username)
    if email_cc:
        message["Cc"] = email_cc
    if email_bcc:
        message["Bcc"] = email_bcc
    message["Subject"] = subject_text

    # Plain text email for fall back
    message.set_content(plain_text_body)

    if html_body:
        message.add_alternative(html_body, subtype="html")
        if venue_image and venue_image_cid:
            message = add_attachment(message, venue_image, venue_image_cid)
        if company_image_cid:
            message = add_attachment(message, "img/company_logo.png", company_image_cid)

    try:
        office365_connection(o365_username, o365_password, message)
    except Exception as error:
        print(
            f'{date.today()} {time.strftime("%H:%M:%S")} An error occurred: {type(error).__name__} {error.args} {error}'
        )
