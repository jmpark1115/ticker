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
price = askprice - 300
# price = askprice
response = bithumb.place(targetCurrency, baseCurrency, units, price, "bid")
print(response)

#time delay
time.sleep(5)

"""
#sell
print("=== sell ===")
units = 10
price = bidprice + 300
response = bithumb.place(targetCurrency, baseCurrency, units, price, "ask")
status = "OK" if response["status"] == "0000" else "ERROR"
print(status)
print(response)
"""

"""
response = my.order_detail(orderNumber, type, targetCurrency)
status = "OK" if response["status"] == "0000" else "ERROR"
print(status)
print(response)

response = my.cancel(type, orderNumber, targetCurrency)
status = "OK" if response["status"] == "0000" else "ERROR"
print(status)
print(response)
"""

"""
response = my.btc_withdrawal(targetCurrency, dest_address_xrp_coinone, units, dest_tag)
status = "OK" if response["status"] == "0000" else "ERROR"
print(status)
print(response)
"""
"""
response = my.krw_deposit()
response = my.krw_withdrawal("090", bankaccount, drawal_price)
status = "OK" if response["status"] == "0000" else "ERROR"
print(status)
print(response)
"""



