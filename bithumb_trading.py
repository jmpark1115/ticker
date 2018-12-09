# 이 프로그램은 지갑에 있는 밸런스를 체크하는 프로그램이다.

from bithumb import Bithumb
from configparser import ConfigParser, NoSectionError
import time

# Load Config File
config = ConfigParser()
config.read('trading.conf')

bithumbKey = config.get('ArbBot', 'bithumbKey')
bithumbSecret = config.get('ArbBot', 'bithumbSecret')

targetCurrency = 'XRP'
baseCurrency   = 'KRW'

# object created
bithumb = Bithumb(bithumbKey, bithumbSecret)

#balance check
print("=== check balance ===")
walletinfo = bithumb.balance(targetCurrency)
print(walletinfo)

#check orderbook
marketinfo = bithumb.orderbook(targetCurrency)
print(marketinfo)
askprice = float(marketinfo["data"]["asks"][0]["price"])
bidprice = float(marketinfo["data"]["bids"][0]["price"])
askqty = float(marketinfo["data"]["asks"][0]["quantity"])
bidqty = float(marketinfo["data"]["bids"][0]["quantity"])
print("askprice[%d] bidprice[%d] askqty[%d] bidqty[%d]"
      %(askprice, bidprice, askqty, bidqty))


#buy
units = 10
price = askprice - 100
# price = askprice
response = bithumb.place(targetCurrency, baseCurrency, units, price, "bid")
print(response)
orderNumber = response['order_id']
print(orderNumber)

#time delay
time.sleep(5)


response = bithumb.order_detail(orderNumber, 'bid', targetCurrency)
print(response)

response = bithumb.cancel('bid', orderNumber, targetCurrency)
print(response)


dest_address_xrp_coinone = your_address
dest_tag = 0
response = bithumb.btc_withdrawal(targetCurrency, dest_address_xrp_coinone, units, dest_tag)
print(response)


bankaccount = your_account
drawal_price = 1000
response = bithumb.krw_deposit()
response = bithumb.krw_withdrawal("090", bankaccount, drawal_price)
print(response)




