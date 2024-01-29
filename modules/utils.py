from inspect import getsourcefile
from random import randint
from requests import post
from loguru import logger
from time import sleep
from tqdm import tqdm
import sys
import ctypes
import os
sys.__stdout__ = sys.stdout # error with `import inquirer` without this string in some system
from inquirer import prompt, List

import settings


logger.remove()
logger.add(sys.stderr, format="<white>{time:HH:mm:ss}</white> | <level>{message}</level>")
windll = ctypes.windll if os.name == 'nt' else None # for Mac users


class WindowName:
    def __init__(self, accs_amount):
        try: self.path = os.path.abspath(getsourcefile(lambda: 0)).split("\\")[-2]
        except: self.path = os.path.abspath(getsourcefile(lambda: 0)).split("/")[-2]

        self.accs_amount = accs_amount
        self.accs_done = 0
        self.modules_amount = 0
        self.modules_done = 0

        self.update_name()

    def update_name(self):
        if os.name == 'nt':
            windll.kernel32.SetConsoleTitleW(f'BeraChain Testnet v1.00 [{self.accs_done}/{self.accs_amount}] | {self.path}')

    def update_accs(self):
        self.accs_done += 1
        self.modules_amount = 0
        self.modules_done = 0
        self.update_name()

    def update_modules(self):
        self.modules_done += 1
        self.update_name()

    def set_modules(self, modules_amount: int):
        self.modules_amount = modules_amount
        self.update_name()


class TgReport:
    def __init__(self):
        self.logs = ''


    def update_logs(self, text: str):
        self.logs += f'{text}\n'


    def send_log(self, wallet, window_name):
        notification_text = f'[{window_name.accs_done}/{window_name.accs_amount}] <i>{wallet.address}</i>\n' \
                            f'{self.logs}\n{wallet.status}'
        texts = []
        while len(notification_text) > 0:
            texts.append(notification_text[:1900])
            notification_text = notification_text[1900:]

        if settings.TG_BOT_TOKEN:
            for tg_id in settings.TG_USER_ID:
                for text in texts:
                    try: post(f'https://api.telegram.org/bot{settings.TG_BOT_TOKEN}/sendMessage?parse_mode=html&chat_id={tg_id}&text={text}')
                    except Exception as err: logger.error(f'[-] TG | Send Telegram message error to {tg_id}: {err}')


def sleeping(*timing):
    if type(timing[0]) == list: timing = timing[0]
    if len(timing) == 2: x = randint(timing[0], timing[1])
    else: x = timing[0]
    for _ in tqdm(range(x), desc='sleep ', bar_format='{desc}: {n_fmt}/{total_fmt}'):
        sleep(1)


def choose_mode():
    questions = [
        List('prefered_path', message="What mode do you prefer?",
             choices=[
                'Onchain actions',
                'Claim quests on Galxe',
             ]
        )
    ]
    path = prompt(questions)['prefered_path']
    return ' '.join(path.split()[:2])


def show_settings():
    settings_dict = {
        'SHUFFLE_WALLETS': 'ПЕРЕМЕШИВАТЬ КОШЕЛЬКИ',
        'PROXY': 'ПРОКСИ',
    }
    max_len = max([len(val) for val in list(settings_dict.values())]) + 2

    print('')

    for key, value in settings_dict.items():
        if key == 'PROXY':
            if getattr(settings, key) not in ['http://log:pass@ip:port', '']:
                logger.info(f'{value}{"".join([" " for _ in range(max_len-len(value))])}|  ДА')
            else:
                logger.critical(f'{value}{"".join([" " for _ in range(max_len-len(value))])}| НЕТ')

        else:
            if getattr(settings, key):
                logger.critical(f'{value}{"".join([" " for _ in range(max_len-len(value))])}|  ДА')
            else:
                logger.info(f'{value}{"".join([" " for _ in range(max_len-len(value))])}| НЕТ')
    print('\n')
    sleep(0.2)
