from random import uniform

from modules.utils import sleeping, logger
from modules.wallet import Wallet
import settings
from .config import TOKEN_ADDRESSES


class Honey(Wallet):
    def __init__(self, wallet: Wallet):
        super().__init__(privatekey=wallet.privatekey, tg_report=wallet.tg_report, browser=wallet.browser, email=wallet.email)

        self.from_chain = 'berachain'
        self.web3 = self.get_web3(self.from_chain)

        self.swap()


    def swap(self, retry=0):
        try:
            module_str = f'honey swap'

            contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address('0x09ec711b81cD27A6466EC40960F2f8D85BB129D9'),
                abi='[{"inputs":[{"internalType":"contractIERC20","name":"_honey","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"erc20Module","outputs":[{"internalType":"contractIERC20Module","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getExchangable","outputs":[{"components":[{"internalType":"contractIERC20","name":"collateral","type":"address"},{"internalType":"bool","name":"enabled","type":"bool"},{"internalType":"uint256","name":"mintRate","type":"uint256"},{"internalType":"uint256","name":"redemptionRate","type":"uint256"}],"internalType":"structERC20Honey.ERC20Exchangable[]","name":"","type":"tuple[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"honey","outputs":[{"internalType":"contractIERC20","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"honeyModule","outputs":[{"internalType":"contractIHoneyModule","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"contractIERC20","name":"collateral","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"mint","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"contractIERC20","name":"collateral","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"previewMint","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"contractIERC20","name":"collateral","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"previewRedeem","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"contractIERC20","name":"collateral","type":"address"}],"name":"redeem","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}]'
            )

            value_usdc_balance = int(
                self.get_balance(chain_name=self.from_chain, token_name='stgUSDC') *
                uniform(settings.USDC_AMOUNT_TO_SWAP[0], settings.USDC_AMOUNT_TO_SWAP[1]) / 100)
            amount_usdc_balance = round(value_usdc_balance / 1e18, 4)
            amount_to_get = round(amount_usdc_balance * 0.995, 4)

            module_str = f'honey swap {amount_usdc_balance} stgUSDC -> {amount_to_get} HONEY'

            self.approve(chain_name=self.from_chain, spender=contract.address, token_name='stgUSDC', value=value_usdc_balance)

            contract_txn = contract.functions.mint(
                self.address,
                TOKEN_ADDRESSES['stgUSDC'],
                value_usdc_balance
            )

            tx_hash = self.sent_tx(chain_name=self.from_chain, tx=contract_txn, tx_label=module_str)
            return tx_hash

        except Exception as error:
            if retry < settings.RETRY:
                logger.error(f'{module_str} | {error}')
                sleeping(10)
                return self.swap(retry=retry+1)
            else:
                self.tg_report.update_logs(f'❌ {module_str}: {error}')
                raise ValueError(f'{module_str}: {error}')
