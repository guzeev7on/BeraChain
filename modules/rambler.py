from bs4 import BeautifulSoup
from imaplib import IMAP4
import imaplib
import email

from modules.utils import logger, sleep
from settings import TO_WAIT_EMAIL


class Rambler:
    def __init__(self, mail_data: str):
        self.mail_data = mail_data
        if mail_data:
            self.mail_login = mail_data.split(':')[0]
            self.mail_pass = mail_data.split(':')[1]
            self.login()


    def login(self):
        try:
            self.imap = imaplib.IMAP4_SSL('imap.rambler.ru')
            self.imap.login(self.mail_login, self.mail_pass)
        except IMAP4.error as error:
            raise Exception(f'[-] Email | Cannot login with {self.mail_login} {self.mail_pass}: {error}')


    def get_code(self):
        first = True
        timer = 0

        self.login()

        while True:
            last_mail_id = self.imap.select('INBOX')[1][0].decode()
            result, data = self.imap.fetch(last_mail_id, "(RFC822)")
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            if msg["From"] != 'Galxe <notify@email.galxe.com>':
                timer += 10 # + 10 seconds
                if timer > TO_WAIT_EMAIL * 60:
                    raise Exception(f'[-] Email | Time to wait mail from Galxe exceed')
                if first:
                    first = False
                    logger.info(f'[ ] Email | Waiting mail from Galxe')
                sleep(10)
                continue

            body = msg.get_payload()
            soup = BeautifulSoup(body, 'html.parser')
            h1_tag = soup.find('h1')
            logger.info(f'[+] Email | Got mail code from Galxe')
            return h1_tag.text # code
