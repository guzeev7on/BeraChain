from random import shuffle
import os

from modules import *
from settings import SLEEP_BETWEEN_ACCS, SHUFFLE_WALLETS


def berachain_onchain(wallet: Wallet):

    if wallet.get_balance(chain_name='berachain') == 0:
        wallet.browser.request_faucet(address=wallet.address) # try to address.lower()
        if wallet.wait_balance(chain_name='berachain', needed_balance=0, only_more=True) != 'not updated':
            raise Exception(f'[-] Web3 | Tokens not arrived from Faucet')

    Bex(wallet=wallet) # BERA -> stgUSDC
    sleeping(10, 20) # задержка между свапами
    Honey(wallet=wallet) # stgUSDC -> HONEY

    return '✅ Swapped two times'


def galxe_quests_confirm(wallet: Wallet):
    signature, text = wallet.get_signature_for_galxe_login()

    wallet.browser.login_in_galxe(address=wallet.address, text=text, signature=signature)
    galxe_acc_info = wallet.browser.get_galaxy_acc_info()

    if galxe_acc_info["email"] == "":
        if wallet.email.mail_data == None: raise Exception(f'[-] Galxe | This wallet doesnt have bound email. You must provide it in .txt for this account')
        wallet.browser.send_email(email=wallet.email.mail_login)
        code = wallet.email.get_code()
        wallet.browser.confirm_email(email=wallet.email.mail_login, code=code)
    else:
        logger.info(f'[+] Galxe | Already bound email "{galxe_acc_info["email"]}"')

    wallet.browser.open_faucet()
    if wallet.browser.reload_task(cred_id="367886459336302592") == True:
        return wallet.browser.claim()


def run_accs(accs_data: list):
    funcs_dct = {
        'Onchain actions': berachain_onchain,
        'Claim quests': galxe_quests_confirm,
    }

    for acc in accs_data:
        try:
            windowname.update_accs()
            browser = Browser()
            tg_report = TgReport()
            email = Rambler(mail_data=acc['mail_data'])
            wallet = Wallet(privatekey=acc['privatekey'], tg_report=tg_report, browser=browser, email=email)

            logger.info(f'[{windowname.accs_done}/{windowname.accs_amount}] {wallet.address}')

            wallet.status = funcs_dct[MODE](wallet=wallet)

        except Exception as err:
            wallet.status = '❌ ' + str(err)
            logger.error(str(err))

        finally:
            excel.edit_table(wallet=wallet)
            tg_report.send_log(wallet=wallet, window_name=windowname)
            sleeping(SLEEP_BETWEEN_ACCS[0], SLEEP_BETWEEN_ACCS[1]) # задержка между аккаунтами


if __name__ == '__main__':
    if not os.path.isdir('results'): os.mkdir('results')
    with open('privatekeys.txt') as f: p_keys = f.read().splitlines()
    with open('emails.txt') as f: mails_data = f.read().splitlines()

    show_settings()

    MODE = choose_mode()
    if MODE == 'Claim quests' and len(mails_data) != 0:
        if len(p_keys) != len(mails_data):
            raise Exception(f'Private keys amount must be equals emails! {len(p_keys)} != {len(mails_data)}. Or remove all emails from .txt')
        accs_data = [{'privatekey': pk, 'mail_data': mail_data} for pk, mail_data in zip(p_keys, mails_data)]
    else:
        accs_data = [{'privatekey': pk, 'mail_data': None} for pk in p_keys]

    excel = Excel(total_len=len(p_keys))
    windowname = WindowName(len(p_keys))
    if SHUFFLE_WALLETS: shuffle(accs_data)

    try:
        run_accs(accs_data=accs_data)
    except Exception as err:
        logger.error(f'Global error: {err}')

    logger.success(f'All accs done.\n\n')
    sleep(0.1)
    input(' > Exit')
