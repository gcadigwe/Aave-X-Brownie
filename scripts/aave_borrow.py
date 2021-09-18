from brownie.network import web3
from scripts.get_weth import get_weth
from scripts.helpful_scripts import get_account
from brownie import config,network,interface
from web3 import Web3

amount = Web3.toWei(0.1,'ether')


def main():
  account = get_account()
  erc20_address = config['networks'][network.show_active()]['weth_token']
  if network.show_active() in ['mainnet-fork']:
    get_weth()
  lending_pool = get_lending_pool()
  print(f'{lending_pool}')
  # Approve sending token
  approve_erc20(amount,lending_pool.address,erc20_address,account)
  deposit_erc20(erc20_address,amount,account.address,0)

  borrowable_eth, total_debt = get_borrowable_data(lending_pool,account)

  print("Let's borrow!")
  dai_eth_price = get_asset_price(config['networks'][network.show_active()]['dai_eth_price_feed'])
  print(f'Dai/Eth price above')

  amount_dai_to_borrow = (1/dai_eth_price) * (borrowable_eth * 0.95)

  print(f'what to borrow {amount_dai_to_borrow}')
  dai_address = config['networks'][network.show_active()]['dai_token']
  borrow_tx = lending_pool.borrow(dai_address, Web3.toWei(amount_dai_to_borrow,'ether'),1,0,account.address,{'from':account})
  borrow_tx.wait(1)
  print('borrowed some dai')
  repay_all(amount,lending_pool,account)
  print('You just deposited, borrowed and repayed with aave')


def repay_all(amount, lending_pool,account):
  approve_erc20(Web3.toWei(amount,'ether'), lending_pool, config['networks'][network.show_active()]['dai_token'],account)
  repay_tx = lending_pool.repay(config['networks'][network.show_active()]['dai_token'], amount,1,account.address, {'from':account})
  repay_tx.wait(1)



# def get_asset_price(dai_eth_price_feed):
#   price = get_asset_price(config['networks'][network.show_active()]['dai_eth_price_feed'])


def get_borrowable_data(lending_pool,account):
  (test_collateral_eth, total_debt_eth,available_borrow_eth,current_liquidation_threshold,ltv,health_factor) = lending_pool.getUserAccountData(account.address)

  available_borrow_eth = Web3.fromWei(available_borrow_eth,'ether')
  test_collateral_eth = Web3.fromWei(test_collateral_eth,'ether')
  total_debt_eth = Web3.fromWei(total_debt_eth, 'ether')

  print(f'You have {available_borrow_eth} worth of ETH deposited')
  print(f'You have {test_collateral_eth} collataral ETH')
  print(f'You have {total_debt_eth} total Debt ETH')
  return (float(available_borrow_eth),float(total_debt_eth))


def get_lending_pool():
  lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
    config['networks'][network.show_active()]['lending_pool_addresses_provider']
  )

  lending_pool_address = lending_pool_addresses_provider.getLendingPool()
  lending_pool = interface.ILendingPool(lending_pool_address)
  return lending_pool


def approve_erc20(amount,spender,erc20_address,account):
  print('approving erc20 tokenk')
  erc20 = interface.IERC20(erc20_address)
  tx = erc20.approve(spender,amount,{'from':account})
  tx.wait(1)
  print('Approved')
  return tx


def deposit_erc20(address,amount,accountAddress,referralCode):
  account = get_account()
  lending_pool = get_lending_pool()
  tx = lending_pool.deposit(address,amount,accountAddress,referralCode,{'from':account})
  print('deposit complete')
  tx.wait(1)

def get_asset_price(price_feed_address):
  dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
  latest_price = dai_eth_price_feed.latestRoundData()[1]
  converted = Web3.fromWei(latest_price,'ether')
  return float(converted)