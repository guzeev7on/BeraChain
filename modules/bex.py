from random import uniform

from modules.utils import sleeping, logger, sleep
from modules.wallet import Wallet
import settings


class Bex(Wallet):
    def __init__(self, wallet: Wallet):
        super().__init__(privatekey=wallet.privatekey, tg_report=wallet.tg_report, browser=wallet.browser, email=wallet.email)

        self.from_chain = 'berachain'
        self.web3 = self.get_web3(self.from_chain)

        self.swap()


    def swap(self, retry=0):
        try:
            module_str = f'bex swap BERA -> stgUSDC'

            old_balance = self.get_balance(chain_name='berachain', token_name='stgUSDC', human=True)

            amount_to_swap = round(uniform(settings.BERA_AMOUNT_TO_SWAP[0], settings.BERA_AMOUNT_TO_SWAP[1]), 3)
            value_to_swap = int(amount_to_swap * 1e18)
            module_str = f'bex swap {amount_to_swap} BERA -> stgUSDC'

            quotes = self.browser.quote_swap(value_to_swap=value_to_swap)
            amount_to_get = round(int(quotes['amountOut']) * (0.75 - (retry * 0.05)) / 1e18, 6)
            if amount_to_get == 0:
                logger.warning(f'[-] Web3 | bex api bad response, trying again')
                sleep(5)
                return self.swap(retry=retry)
            module_str = f'bex swap {amount_to_swap} BERA -> {amount_to_get} stgUSDC'

            contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address('0x0d5862FDbdd12490f9b4De54c236cff63B038074'),
                abi='[{"inputs":[{"internalType":"address","name":"pool","type":"address"},{"internalType":"address","name":"receiver","type":"address"},{"internalType":"address[]","name":"assetsIn","type":"address[]"},{"internalType":"uint256[]","name":"amountsIn","type":"uint256[]"}],"name":"addLiquidity","outputs":[{"internalType":"address[]","name":"shares","type":"address[]"},{"internalType":"uint256[]","name":"shareAmounts","type":"uint256[]"},{"internalType":"address[]","name":"liquidity","type":"address[]"},{"internalType":"uint256[]","name":"liquidityAmounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"enumIERC20DexModule.SwapKind","name":"kind","type":"uint8"},{"components":[{"internalType":"address","name":"poolId","type":"address"},{"internalType":"address","name":"assetIn","type":"address"},{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address","name":"assetOut","type":"address"},{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"bytes","name":"userData","type":"bytes"}],"internalType":"structIERC20DexModule.BatchSwapStep[]","name":"swaps","type":"tuple[]"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"batchSwap","outputs":[{"internalType":"address[]","name":"assets","type":"address[]"},{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"string","name":"name","type":"string"},{"internalType":"address[]","name":"assetsIn","type":"address[]"},{"internalType":"uint256[]","name":"amountsIn","type":"uint256[]"},{"internalType":"string","name":"poolType","type":"string"},{"components":[{"components":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"weight","type":"uint256"}],"internalType":"structIERC20DexModule.AssetWeight[]","name":"weights","type":"tuple[]"},{"internalType":"uint256","name":"swapFee","type":"uint256"}],"internalType":"structIERC20DexModule.PoolOptions","name":"options","type":"tuple"}],"name":"createPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"pool","type":"address"},{"internalType":"address","name":"baseAsset","type":"address"},{"internalType":"address","name":"quoteAsset","type":"address"}],"name":"getExchangeRate","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"pool","type":"address"}],"name":"getLiquidity","outputs":[{"internalType":"address[]","name":"asset","type":"address[]"},{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"pool","type":"address"}],"name":"getPoolName","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"pool","type":"address"}],"name":"getPoolOptions","outputs":[{"components":[{"components":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"weight","type":"uint256"}],"internalType":"structIERC20DexModule.AssetWeight[]","name":"weights","type":"tuple[]"},{"internalType":"uint256","name":"swapFee","type":"uint256"}],"internalType":"structIERC20DexModule.PoolOptions","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"pool","type":"address"},{"internalType":"address[]","name":"assets","type":"address[]"},{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"name":"getPreviewAddLiquidityNoSwap","outputs":[{"internalType":"address[]","name":"shares","type":"address[]"},{"internalType":"uint256[]","name":"shareAmounts","type":"uint256[]"},{"internalType":"address[]","name":"liqOut","type":"address[]"},{"internalType":"uint256[]","name":"liquidityAmounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"pool","type":"address"},{"internalType":"address[]","name":"liquidity","type":"address[]"},{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"name":"getPreviewAddLiquidityStaticPrice","outputs":[{"internalType":"address[]","name":"shares","type":"address[]"},{"internalType":"uint256[]","name":"shareAmounts","type":"uint256[]"},{"internalType":"address[]","name":"liqOut","type":"address[]"},{"internalType":"uint256[]","name":"liquidityAmounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"enumIERC20DexModule.SwapKind","name":"kind","type":"uint8"},{"components":[{"internalType":"address","name":"poolId","type":"address"},{"internalType":"address","name":"assetIn","type":"address"},{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address","name":"assetOut","type":"address"},{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"bytes","name":"userData","type":"bytes"}],"internalType":"structIERC20DexModule.BatchSwapStep[]","name":"swaps","type":"tuple[]"}],"name":"getPreviewBatchSwap","outputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"pool","type":"address"},{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"getPreviewBurnShares","outputs":[{"internalType":"address[]","name":"assets","type":"address[]"},{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"pool","type":"address"},{"internalType":"address[]","name":"assets","type":"address[]"},{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"name":"getPreviewSharesForLiquidity","outputs":[{"internalType":"address[]","name":"shares","type":"address[]"},{"internalType":"uint256[]","name":"shareAmounts","type":"uint256[]"},{"internalType":"address[]","name":"liquidity","type":"address[]"},{"internalType":"uint256[]","name":"liquidityAmounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"pool","type":"address"},{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"getPreviewSharesForSingleSidedLiquidityRequest","outputs":[{"internalType":"address[]","name":"assets","type":"address[]"},{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"enumIERC20DexModule.SwapKind","name":"kind","type":"uint8"},{"internalType":"address","name":"pool","type":"address"},{"internalType":"address","name":"baseAsset","type":"address"},{"internalType":"uint256","name":"baseAssetAmount","type":"uint256"},{"internalType":"address","name":"quoteAsset","type":"address"}],"name":"getPreviewSwapExact","outputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"pool","type":"address"},{"internalType":"address","name":"assetIn","type":"address"},{"internalType":"uint256","name":"assetAmount","type":"uint256"}],"name":"getRemoveLiquidityExactAmountOut","outputs":[{"internalType":"address[]","name":"assets","type":"address[]"},{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"pool","type":"address"},{"internalType":"address","name":"assetOut","type":"address"},{"internalType":"uint256","name":"sharesIn","type":"uint256"}],"name":"getRemoveLiquidityOneSideOut","outputs":[{"internalType":"address[]","name":"assets","type":"address[]"},{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"pool","type":"address"}],"name":"getTotalShares","outputs":[{"internalType":"address[]","name":"assets","type":"address[]"},{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"pool","type":"address"},{"internalType":"address","name":"withdrawAddress","type":"address"},{"internalType":"address","name":"assetIn","type":"address"},{"internalType":"uint256","name":"amountIn","type":"uint256"}],"name":"removeLiquidityBurningShares","outputs":[{"internalType":"address[]","name":"liquidity","type":"address[]"},{"internalType":"uint256[]","name":"liquidityAmounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"pool","type":"address"},{"internalType":"address","name":"withdrawAddress","type":"address"},{"internalType":"address","name":"assetOut","type":"address"},{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address","name":"sharesIn","type":"address"},{"internalType":"uint256","name":"maxSharesIn","type":"uint256"}],"name":"removeLiquidityExactAmount","outputs":[{"internalType":"address[]","name":"shares","type":"address[]"},{"internalType":"uint256[]","name":"shareAmounts","type":"uint256[]"},{"internalType":"address[]","name":"liquidity","type":"address[]"},{"internalType":"uint256[]","name":"liquidityAmounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"enumIERC20DexModule.SwapKind","name":"kind","type":"uint8"},{"internalType":"address","name":"poolId","type":"address"},{"internalType":"address","name":"assetIn","type":"address"},{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address","name":"assetOut","type":"address"},{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swap","outputs":[{"internalType":"address[]","name":"assets","type":"address[]"},{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"}]'
            )

            contract_txn = contract.functions.batchSwap(
                    0,
                    [(
                        self.web3.to_checksum_address(quotes['pool']),
                        "0x0000000000000000000000000000000000000000",
                        value_to_swap,
                        self.web3.to_checksum_address(quotes['assetOut']),
                        int(int(quotes['amountOut']) * 0.75),
                        "0x"
                    )],
                    99999999, # "deadline"
            )

            tx_hash = self.sent_tx(chain_name=self.from_chain, tx=contract_txn, tx_label=module_str, value=value_to_swap)
            if self.wait_balance(chain_name='berachain', token_name='stgUSDC', needed_balance=old_balance, only_more=True) == 'not updated':
                if retry < settings.RETRY:
                    return self.swap(retry=retry+1)
                else:
                    self.tg_report.update_logs(f'❌ {module_str}: balance not updated')
                    raise ValueError(f'{module_str}: balance not updated')
            return tx_hash

        except Exception as error:
            if retry < settings.RETRY:
                logger.error(f'{module_str} | {error}')
                sleeping(10)
                return self.swap(retry=retry+1)
            else:
                self.tg_report.update_logs(f'❌ {module_str}: {error}')
                raise ValueError(f'{module_str}: {error}')
