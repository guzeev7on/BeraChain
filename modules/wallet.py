from web3.middleware import geth_poa_middleware
from eth_account.messages import encode_defunct
from random import choice, randint
from string import ascii_letters, digits
from datetime import datetime, timezone, timedelta
from typing import Union, Optional
from time import sleep
from web3 import Web3

from modules.utils import logger, sleeping
import modules.config as config
import settings


class Wallet:
    def __init__(self, privatekey: str, tg_report, browser, email):
        self.privatekey = privatekey
        self.game_email = ''
        self.game_username = ''
        self.game_password = ''

        self.account = Web3().eth.account.from_key(privatekey)
        self.address = self.account.address
        self.tg_report = tg_report
        self.browser = browser
        self.email = email

        self.max_retries = 5
        self.status = ''


    def get_web3(self, chain_name: str):
        if settings.PROXY not in ['http://log:pass@ip:port', '']:
            web3 = Web3(Web3.HTTPProvider(
                settings.RPCS[chain_name],
                request_kwargs={"proxies": {'https': settings.PROXY, 'http': settings.PROXY}}
            ))
        else:
            web3 = Web3(Web3.HTTPProvider(settings.RPCS[chain_name]))
        web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        return web3


    def get_gas(self, chain_name):
        if chain_name == 'linea': return {'gasPrice': self.get_web3(chain_name=chain_name).eth.gas_price}
        max_priority = self.get_web3(chain_name=chain_name).eth.max_priority_fee
        last_block = self.get_web3(chain_name=chain_name).eth.get_block('latest')
        base_fee = last_block['baseFeePerGas']
        block_filled = last_block['gasUsed'] / last_block['gasLimit'] * 100
        if block_filled > 50: base_fee *= 1.127
        max_fee = int(base_fee + max_priority)

        return {'maxPriorityFeePerGas': max_priority, 'maxFeePerGas': max_fee}


    def approve(self, chain_name: str, spender: str, token_name: Optional[str] = False, token_address: Optional[str] = False, amount=None, value=None, retry=0):
        try:
            module_str = f'approve {token_name} to {spender}'

            web3 = self.get_web3(chain_name=chain_name)
            spender = web3.to_checksum_address(spender)
            if token_name: token_address = config.TOKEN_ADDRESSES[token_name]
            token_contract = web3.eth.contract(address=web3.to_checksum_address(token_address),
                                         abi='[{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}]')
            if not token_name:
                token_name = token_contract.functions.name().call()
                module_str = f'approve {token_name} to {spender}'

            decimals = token_contract.functions.decimals().call()
            if amount:
                value = int(amount * 10 ** decimals)
                new_amount = round(amount * randint(10, 40), 5)
                new_value = int(new_amount * 10 ** decimals)
            else:
                new_value = int(value * randint(10, 40))
                new_amount = round(new_value / 10 ** decimals, 5)
            module_str = f'approve {new_amount} {token_name} to {spender}'

            allowance = token_contract.functions.allowance(self.address, spender).call()
            if allowance < value:
                tx = token_contract.functions.approve(spender, new_value)
                tx_hash = self.sent_tx(chain_name=chain_name, tx=tx, tx_label=module_str)
                sleeping(20, 40)
                return tx_hash
        except Exception as error:
            if retry < settings.RETRY:
                logger.error(f'{module_str} | {error}')
                logger.info(f'try again | {self.address}')
                sleeping(10)
                self.approve(chain_name=chain_name, token_name=token_name, spender=spender, amount=amount, value=value, retry=retry+1)
            else:
                self.tg_report.update_logs(f'❌ {module_str}: {error}')
                raise ValueError(f'{module_str}: {error}')


    def sent_tx(self, chain_name: str, tx, tx_label, tx_raw=False, value=0):
        try:
            web3 = self.get_web3(chain_name=chain_name)
            if not tx_raw:
                if type(tx) != dict:
                    tx = tx.build_transaction({
                        'from': self.address,
                        'chainId': web3.eth.chain_id,
                        'nonce': web3.eth.get_transaction_count(self.address),
                        'value': value,
                        **self.get_gas(chain_name=chain_name),
                    })


            signed_tx = web3.eth.account.sign_transaction(tx, self.privatekey)
            raw_tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash = web3.to_hex(raw_tx_hash)
            tx_link = f'{config.CHAINS_DATA[chain_name]["explorer"]}{tx_hash}'
            logger.debug(f'[•] Web3 | {tx_label} tx sent: {tx_link}')

            status = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=int(settings.TO_WAIT_TX * 60)).status

            if status == 1:
                logger.info(f'[+] Web3 | {tx_label} tx confirmed\n')
                self.tg_report.update_logs(f'✅ {tx_label}')
                return tx_hash
            else:
                # if not retry:
                #     logger.debug(f'trying to resend transaction with higher gas')
                #     sleep(5)
                #     return self.sent_tx(chain_name=chain_name, tx=tx, tx_label=tx_label, tx_raw=tx_raw, value=value, retry=True)
                # else:
                self.tg_report.update_logs(f'❌ {tx_label} <a href="{tx_link}">TX</a>')
                raise ValueError(f'tx failed: {tx_link}')

        except Exception as err:
            if 'already known' in str(err):
                try: raw_tx_hash
                except: raw_tx_hash = ''
                logger.warning(f'{tx_label} | Couldnt get tx hash, thinking tx is success ({raw_tx_hash})')
                sleeping(15)
                return True

            try: encoded_tx = f'\nencoded tx: {tx._encode_transaction_data()}'
            except: encoded_tx = ''
            raise ValueError(f'tx failed error: {err}{encoded_tx}')


    def get_balance(self, chain_name: str, token_name=False, token_address=False, human=False):
        web3 = self.get_web3(chain_name=chain_name)
        if token_name: token_address = config.TOKEN_ADDRESSES[token_name]
        if token_address: contract = web3.eth.contract(address=web3.to_checksum_address(token_address),
                                     abi='[{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}]')
        while True:
            try:
                if token_address: balance = contract.functions.balanceOf(self.address).call()
                else: balance = web3.eth.get_balance(self.address)

                decimals = contract.functions.decimals().call() if token_address else 18
                if not human: return balance
                return balance / 10 ** decimals
            except Exception as err:
                logger.warning(f'[•] Web3 | Get balance error: {err}')
                sleep(5)


    def wait_balance(self, chain_name: str, needed_balance: Union[int, float], only_more: bool = False, token_name: Optional[str] = False, token_address: Optional[str] = False):
        " needed_balance: human digit "
        if token_name:
            token_address = config.TOKEN_ADDRESSES[token_name]

        elif token_address:
            contract = self.get_web3(chain_name=chain_name).eth.contract(address=Web3().to_checksum_address(token_address),
                                         abi='[{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}]')
            token_name = contract.functions.name().call()

        else:
            token_name = 'BERA'

        if only_more: logger.debug(f'[•] Web3 | Waiting for balance more than {round(needed_balance, 6)} {token_name} in {chain_name.upper()}')
        else: logger.debug(f'[•] Web3 | Waiting for {round(needed_balance, 6)} {token_name} balance in {chain_name.upper()}')

        while True:
            try:
                new_balance = self.get_balance(chain_name=chain_name, human=True, token_address=token_address)

                if only_more: status = new_balance > needed_balance
                else: status = new_balance >= needed_balance
                if status:
                    logger.debug(f'[•] Web3 | New balance: {round(new_balance, 6)} {token_name}\n')
                    return new_balance
                sleep(5)
            except Exception as err:
                logger.warning(f'[•] Web3 | Wait balance error: {err}')
                sleep(10)


    def get_signature_for_galxe_login(self):
        nonce = ''.join([choice(ascii_letters + digits) for _ in range(17)])
        now_utc = datetime.now(timezone.utc)
        issued_at = now_utc.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        exp_at = (now_utc + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        text = f"galxe.com wants you to sign in with your Ethereum account:\n{self.address}\n\n" \
               f"Sign in with Ethereum to the app.\n\nURI: https://galxe.com\nVersion: 1\nChain ID: 1\n" \
               f"Nonce: {nonce}\nIssued At: {issued_at}\nExpiration Time: {exp_at}"

        message = encode_defunct(text=text)
        signed_message = self.account.sign_message(message)
        return signed_message.signature.hex(), text
