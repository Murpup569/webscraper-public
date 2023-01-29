"""Email error message to System Administrator"""
import os

from webscraper.send_o365_email import o365_send_email


def log_error(message):
    """Send email to System Administrator"""
    o365_username = os.getenv("O365USERNAME")
    o365_password = os.getenv("O365PASSWORD")
    recipient_email = "example@example.com"
    subject_email = "ERROR: Something went wrong!"
    o365_send_email(
        o365_username,
        o365_password,
        recipient_email,
        subject_email,
        plain_text_body=message
    )
