import os
import smtplib

# For gmail, generate and use an app specific password
# Store the password as environment variable
my_email = "satya.evolfast@gmail.com"  # Replace with your own gmail
my_password = os.environ.get("MY_PASSWORD")  # For gmail, generate and use an app specific password


class Notification:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"

    def send_email(self, mail_text, fetcher_email):
        with smtplib.SMTP(self.smtp_server) as connection:
            connection.ehlo()
            connection.starttls()
            connection.login(user=my_email, password=my_password)
            connection.sendmail(from_addr=my_email,
                                to_addrs=fetcher_email,  # The email will go to the user configured as fetcher
                                msg=f"Subject: Coffee Order Summary!\n\n{mail_text}")
