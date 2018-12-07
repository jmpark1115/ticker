# import requests
import json
import logging
import time

# from encrypt import decrypt

from urllib.parse import urljoin

from configparser import ConfigParser, NoSectionError

import requests

configFile = "trading.conf"

class Korbit:
    def __init__(self, client_id, secret, production=True, version="v1", timeout=20):
        self.__host = production and "https://api.korbit.co.kr/%s/" % version \
                      or "https://api.korbit-test.com/%s/" % version
        self.exid = "korbit0"
        self.__timeout = timeout
        self.__client_id = client_id
        self.__secret = secret
        self.__token = {}
        self.targetBalance = 0
        self.baseBalance   = 0
        self.askprice = 0
        self.bidprice = 0
        self.askqty = 0
        self.bidqty = 0
        self.taker_fee  = 0.0020
        self.maker_fee  = 0.0008
        self.BCH        = 0.005  # min tradable volume
        self.BTC        = 0.001
        self.ETH        = 0.01
        self.ETC        = 0.01  # GUESS
        self.XRP        = 1
        self.LTC        = 0.01
        # Load Config File
        config = ConfigParser()
        try:
            print('Config File Found! Running in Normal mode!')
            config.read(configFile)
            self.username = config.get('ArbBot', 'userName')
            self.password = config.get('ArbBot', 'passWord')
        except NoSectionError:
            logging.warning('No Config File Found! Running in Drymode!')
            self.username = "noname"
            self.password = "password"

        self.create_token_directly(self.username, self.password)

    # https://apidocs.korbit.co.kr/#public
    def ticker(self, currency_pair="btc_krw"):
        params = {
            'currency_pair': currency_pair
        }
        return self.request_get("ticker", params=params)

    def detailed_ticker(self, currency_pair="btc_krw"):
        params = {
            'currency_pair': currency_pair
        }
        return self.request_get("ticker/detailed", params=params)

    def orderbook(self, currency_pair="btc_krw", category="all", group=True):
        params = {
            'group': group,
            'category': category,
            'currency_pair': currency_pair
        }
        return self.request_get("orderbook", params=params)

    def bids_orderbook(self, currency_pair="btc_krw", group=True):
        return self.orderbook(currency_pair=currency_pair, category="bid", group=group)

    def asks_orderbook(self, currency_pair="btc_krw", group=True):
        return self.orderbook(currency_pair=currency_pair, category="ask", group=group)

    def list_of_filled_orders(self, currency_pair="btc_krw", interval="hour"):
        params = {
            'time': interval,
            'currency_pair': currency_pair
        }
        return self.request_get("transactions", params=params)

    def constants(self):
        return self.request_get("constants")

    def request_get(self, path, headers=None, params=None):
        try:
            response = requests.get(urljoin(self.host, path), headers=headers, params=params, timeout=self.__timeout)
            return response.json()
        except json.decoder.JSONDecodeError as e:
            logging.error("RGet exception: {}, response_text: {}".format(e, response.text))
            if response.status_code == 401:
                logging.error("Needs refresh !!!")
                self.refresh_token()
                response = requests.get(urljoin(self.host, path), headers=self.headers, params=params,
                                        timeout=self.__timeout)
            return response.json()

    def request_post(self, path, headers=None, data=None):
        try:
            response = requests.post(urljoin(self.host, path), headers=headers, data=data, timeout=self.__timeout)
            return response.json()
        except json.decoder.JSONDecodeError as e:
            logging.error("RPexception: {}, response_text: {}".format(e, response.text))
            if response.status_code == 401:
                logging.error("Needs refresh !!!")
                self.refresh_token()
                response = requests.post(urljoin(self.host, path), headers=self.headers, data=data, timeout=self.__timeout)
            return response.json()

    @property
    def host(self):
        return self.__host


    # private api
    # https://apidocs.korbit.co.kr/#authentication
    def create_token_directly(self, username, password):
        payload = {
            'client_id': self.__client_id,
            'client_secret': self.__secret,
            'username': username,
            'password': password,
            'grant_type': "password"
        }
        self.__token = self.request_post("oauth2/access_token", data=payload)
        # print(self.__token)
        return self.__token

    def set_token(self, token):
        self.__token = token

    def refresh_token(self):
        payload = {
            'client_id': self.__client_id,
            'client_secret': self.__secret,
            'refresh_token': self.__token['refresh_token'],
            'grant_type': "refresh_token"
        }
        self.__token = self.request_post("oauth2/access_token", data=payload)
        # print(self.__token)
        return self.__token

    def get_user_info(self):
        return self.request_get("user/info", headers=self.headers)

    @property
    def headers(self):
        # a= "My Authorization {} {}".format(self.__token['token_type'], self.__token['access_token'])
        # print(a)
        # print(self.__token)
        return {
            'Accept': 'application/json',
            'Authorization': "{} {}".format(self.__token['token_type'], self.__token['access_token'])
        }

    def market_bid_order(self, fiat_amount, currency_pair="btc_krw"):
        return self.bid_order('market', fiat_amount=fiat_amount, currency_pair=currency_pair)

    def limit_bid_order(self, coin_amount, price, currency_pair="btc_krw"):
        return self.bid_order('limit', coin_amount=coin_amount, price=price, currency_pair=currency_pair)

    # https://apidocs.korbit.co.kr/#exchange
    def bid_order(self, bid_type, coin_amount=None, price=None, fiat_amount=None, currency_pair="btc_krw"):
        print("BIDDD ORDER")
        payload = {
            'type': bid_type,
            'currency_pair': currency_pair,
            'price': price,
            'coin_amount': coin_amount,
            'fiat_amount': fiat_amount,
            'nonce': self.nonce
        }
        print(payload)
        return self.request_post("user/orders/buy", headers=self.headers, data=payload)

    def ask_order(self, ask_type, coin_amount, price=None, currency_pair="btc_krw"):
        print("ASSSSK ORDER")
        payload = {
            'type': ask_type,
            'currency_pair': currency_pair,
            'price': price,
            'coin_amount': coin_amount,
            'nonce': self.nonce
        }
        print(payload)
        return self.request_post("user/orders/sell", headers=self.headers, data=payload)

    def market_ask_order(self, coin_amount, currency_pair="btc_krw"):
        return self.ask_order('market', coin_amount=coin_amount, currency_pair=currency_pair)

    def limit_ask_order(self, coin_amount, price, currency_pair="btc_krw"):
        return self.ask_order('limit', coin_amount, price, currency_pair)


    def cancel_order(self, ids, currency_pair="btc_krw"):
        payload = {
            'id': ids,
            'currency_pair': currency_pair,
            'nonce': self.nonce
        }
        return self.request_post("user/orders/cancel", headers=self.headers, data=payload)

    def list_open_orders(self, offset=0, limit=10, currency_pair="btc_krw"):
        params = {
            'currency_pair': currency_pair,
            'offset': offset,
            'limit': limit
        }
        return self.request_get("user/orders/open", headers=self.headers, params=params)

    def view_exchange_orders(self, offset, limit, orderNumber, currency_pair="btc_krw"):
        params = {
            'id'           : orderNumber,
            'currency_pair': currency_pair,
            'offset': offset,
            'limit': limit
        }
        return self.request_get("user/orders", headers=self.headers, params=params)

    def view_transfers(self, offset=0, limit=10, currency="btc"):
        params = {
            'currency': currency,
            'offset': offset,
            'limit': limit
        }
        return self.request_get("user/transfers", headers=self.headers, params=params)

    def trading_volume_and_fees(self, currency_pair="all"):
        params = {
            'currency_pair': currency_pair
        }
        return self.request_get("user/volume", headers=self.headers, params=params)

    # https://apidocs.korbit.co.kr/#wallet
    def user_balances(self):
        return self.request_get("user/balances", headers=self.headers)

    def user_accounts(self):
        return self.request_get("user/accounts", headers=self.headers)

    def retrieve_wallet_status(self, currency_pair="btc_krw"):
        params = {
            'currency_pair': currency_pair
        }
        return self.request_get("user/wallet", headers=self.headers, params=params)

    def assign_btc_address(self, currency="btc"):
        payload = {
            'currency': currency,
            'nonce': self.nonce
        }
        return self.request_post("user/coins/address/assign", headers=self.headers, data=payload)

    def request_btc_withdrawal(self, address, amount, currency="btc"):
        payload = {
            'address': address,
            'amount': amount,
            'currency': currency,
            'fee_priority' : 'saver',
            'nonce': self.nonce,
        }
        return self.request_post("user/coins/out", headers=self.headers, data=payload)

    def status_of_btc_deposit_and_transfer(self, transfer_id="", currency="btc"):
        params = {
            'currency': currency
        }
        if transfer_id != "":
            params['id'] = transfer_id

        return self.request_get("user/coins/status", headers=self.headers, params=params)

    def cancel_btc_transfer_request(self, transfer_id, currency="btc"):
        payload = {
            'id': transfer_id,
            'currency': currency,
            'nonce': self.nonce
        }
        return self.request_post("user/coins/out/cancel", headers=self.headers, data=payload)

    @property
    def nonce(self):
        return int(time.time() * 1000)

    def get_order_info(self, currency):
        params     = currency.lower() + '_' + 'krw'
        marketinfo = self.orderbook(params)
        self.askprice = float(marketinfo['asks'][0][0])
        self.bidprice = float(marketinfo['bids'][0][0])
        self.askqty   = float(marketinfo['asks'][0][1])
        self.bidqty   = float(marketinfo['bids'][0][1])


    def get_balance_info(self, currency):
        try:
            balance = self.user_balances()
        except:
            logging.debug("get balance info fail")
        else:
            self.targetBalance = (float)(balance[currency.lower()]['available'])
            self.baseBalance   = (float)(balance['krw'.lower()]['available'])

    def sell(self, currency, coin_amount, price):
        response = self.limit_ask_order(str(coin_amount), str((int)(price)), currency_pair=currency.lower() + '_krw')
        status = "OK" if response["status"] == "success" else "ERROR"
        orderNumber = response.get("orderId", "orderID is not key")
        return status, orderNumber, response

    def buy(self, currency, coin_amount, price):
        response = self.limit_bid_order(str(coin_amount), str((int)(price)), currency_pair=currency.lower() + '_krw')
        status = "OK" if response["status"] == "success" else "ERROR"
        orderNumber = response.get("orderId", "orderID is not key")
        return status, orderNumber, response

    def review_cancel_order(self, orderNumber, type, currency, price, qty):
        params = currency.lower() + '_' + 'krw'
        units_traded = 0
        count = 0
        while True:
            count += 1
            response = self.view_exchange_orders(0, 10, orderNumber, params)
            print("ko: response %s" %response)
            if response[0]["id"] == str(orderNumber):
                if response[0]["status"] != "filled" :
                    if count < 10:
                        print("loop %d" % count)
                        continue
                    else:
                        units_traded = (float)(response[0]["filled_amount"])
                        print("units_traded %.4f" % units_traded)
                        response = self.cancel_order(orderNumber, params)
                        print("ko %s" % response)
                        return "NG", (qty - units_traded)
                else:
                    return "GO", qty
            else:
                print("id number not exist")
                return "NG", 0