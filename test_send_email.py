# -*- coding: utf-8 -*-
"""
Created on Tue Mar 11 17:02:20 2025

@author: edkwa
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_notification(subject, body, to_email):
    """
    Sends an email notification using Gmail SMTP.

    Args:
        subject (str): The subject of the email.
        body (str): The body of the email.
        to_email (str): The recipient's email address.
    """
    try:
        # Retrieve email credentials from environment variables
        from_email = os.getenv('STOCK_TRACKER_EMAIL_FROM')  # Sender email (e.g., flaskstocktracker@gmail.com)
        password = os.getenv('STOCK_TRACKER_EMAIL_PASSWORD')  # App password or less secure apps password

        # Debugging: Print the environment variables
        print(f"STOCK_TRACKER_EMAIL_FROM: {from_email}")
        print(f"STOCK_TRACKER_EMAIL_PASSWORD: {password}")

        # Validate environment variables
        if not from_email or not password:
            logging.error("Email credentials are not set in environment variables.")
            return

        # Create the email
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send the email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(from_email, password)
            server.sendmail(from_email, to_email, msg.as_string())
        logging.info(f"Email sent to {to_email}: {subject}")
    except smtplib.SMTPAuthenticationError:
        logging.error("Failed to authenticate. Check your email credentials.")
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error occurred: {e}")
    except Exception as e:
        logging.error(f"Failed to send email to {to_email}: {e}")

# Test the function
if __name__ == '__main__':
    send_notification(
        subject="Test Notification",
        body="This is a test email from the Flask Stock Tracker.",
        to_email="edkwan1@gmail.com"  # Replace with your email address
    )