import smtplib

my_email = "satya.sahoo@bridgecont.com"
my_password = "*******"


class Notification:
    def __init__(self):
        self.smtp_server = ""

    def send_email(self, mail_text, fetcher_email):
        with smtplib.SMTP("smtp.ionos.de", 587) as connection:
            connection.starttls()
            connection.login(user=my_email, password=my_password)
            connection.sendmail(from_addr=my_email,
                                to_addrs=fetcher_email,
                                msg=f"Subject: Coffee Order Summary!\n\n{mail_text}")
