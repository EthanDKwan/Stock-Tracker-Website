# -*- coding: utf-8 -*-
"""
Created on Mon Mar 17 16:40:39 2025

@author: edkwa
"""

import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv

def send_notification(subject, body, to_email):
    """
    Sends an email notification using Gmail SMTP.

    Args:
        subject (str): The subject of the email.
        body (str): The body of the email.
        to_email (str): The recipient's email address.
    """
    try:
        load_dotenv()
        
        email_from = os.getenv('STOCK_TRACKER_EMAIL_FROM')
        email_password = os.getenv('STOCK_TRACKER_EMAIL_PASSWORD')
        # Validate environment variables
        if not email_from or not email_password:
            logging.error("Email credentials are not set in environment variables.")
            return
        # Create the email
        msg = MIMEMultipart()
        msg['From'] = "Stock Tracker Website <{}>".format(email_from)
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        # Send the email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(email_from, email_password)
            server.sendmail(email_from, to_email, msg.as_string())
        logging.info(f"Email sent to {to_email}: {subject}")
    except smtplib.SMTPAuthenticationError:
        logging.error("Failed to authenticate. Check your email credentials.")
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error occurred: {e}")
    except Exception as e:
        logging.error(f"Failed to send email to {to_email}: {e}")