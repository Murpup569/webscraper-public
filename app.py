"""System module"""
import io
import os
from datetime import date, timedelta
from email.utils import make_msgid
from time import sleep

import pandas as pd
from jinja2 import Environment, FileSystemLoader
from tabulate import tabulate

from webscraper.email_developer import log_error
from webscraper.file_handler import env_check, file_check, load_json
from webscraper.filter_data import (add_dollar_sign_and_format_negative,
                                    clean_currency, create_sum_table,
                                    format_data_to_list, get_location_share)
from webscraper.http_calendar import http_request
from webscraper.send_o365_email import o365_send_email

if __name__ == "__main__":

    # Check files exist
    file_check("json/screensizedata.json")
    file_check("json/config.json")
    file_check("img/company_logo.png")
    venue_data = load_json("json/config.json")
    for venue in venue_data:
        file_check(f'templates/{venue_data[venue]["template_file"]}')
        file_check(venue_data[venue]["logo_file"])

    # Load all external data and set variables
    external_data = {}
    external_data["ScreenSize"] = load_json("json/screensizedata.json")
    external_data["TEXTBOXUSERID"] = os.getenv("TEXTBOXUSERID")
    external_data["TEXTBOXPASSWORD"] = os.getenv("TEXTBOXPASSWORD")
    o365_username = os.getenv("O365USERNAME")
    o365_password = os.getenv("O365PASSWORD")
    URL = os.getenv("URL")
    env_check(external_data["TEXTBOXUSERID"])
    env_check(external_data["TEXTBOXPASSWORD"])
    env_check(URL)
    env_check(o365_username)
    env_check(o365_username)
    env_check(o365_password)
    file_loader = FileSystemLoader("templates")
    env = Environment(loader=file_loader)
    yesterday = date.today() - timedelta(days=1)

    try:
        # Login, navigate, and download CSV from website
        response = http_request(URL, external_data)
    except Exception as error_message:
        log_error(error_message)

    # Format data
    df_original = pd.read_csv(io.StringIO(response.decode("utf-8")))
    for venue in venue_data:
        df_venue = df_original.loc[df_original["VenueName"] == venue]
        df_venue_clean = clean_currency(df_venue)
        df_venue_clean["Location_Share"] = df_venue_clean["NetTerminalIncome"].apply(
            get_location_share
        )
        table = format_data_to_list(add_dollar_sign_and_format_negative(df_venue_clean))
        table.append(create_sum_table(df_venue_clean, yesterday))
        template = env.get_template(venue_data[venue]["template_file"])
        company_image_cid = make_msgid(domain=o365_username.split("@")[1])
        venue_image_cid = make_msgid(domain=o365_username.split("@")[1])

        plain_text_body = f"""\
        \nBelow is the daily report for {venue} of {yesterday}:\
        \n{tabulate(table)}"""

        html_body = template.render(
            venue=venue,
            df_venue=df_venue,
            table=table,
            date=str(yesterday),
            company_image_cid=company_image_cid,
            venue_image_cid=venue_image_cid,
        )

        # Send email
        RECIPIENT_EMAIL = venue_data[venue]["recepient_email"]
        SUBJECT_EMAIL = f"Daily Report {yesterday}"
        EMAIL_CC = venue_data[venue]["email_cc"]
        EMAIL_BCC = venue_data[venue]["email_bcc"]
        VENUE_IMAGE = venue_data[venue]["logo_file"]
        o365_send_email(
            o365_username,
            o365_password,
            RECIPIENT_EMAIL,
            SUBJECT_EMAIL,
            plain_text_body=plain_text_body,
            html_body=html_body,
            email_cc=EMAIL_CC,
            venue_image=VENUE_IMAGE,
            venue_image_cid=venue_image_cid,
            company_image_cid=company_image_cid,
        )
        sleep(1)
