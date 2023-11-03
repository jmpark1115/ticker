# -*- coding: utf-8 -*-
import base64
import json
import hashlib
import hmac
import requests
import time
import logging

base_url = 'https://api.coinone.co.kr/'
error_code = {
    '11': "Access token is missing",
    '12': "Invalid access token",
    '40': "Invalid API permission",
    '50': "Authenticate error",
    '51': "Invalid API",
    '100': "Session expired",
    '101': "Invalid format",
    '102': "ID is not exist",
    '103': "Lack of Balance",
    '104': "Order id is not exist",
    '105': "Price is not correct",
    '106': "Locking error",
    '107': "Parameter error",
    '111': "Order id is not exist",
    '112': "Cancel failed",
    '113': "Quantity is too low(ETH, ETC > 0.01)",
    '120': "V2 API payload is missing",
    '121': "V2 API signature is missing",
    '122': "V2 API nonce is missing",
    '123': "V2 API signature is not correct",
    '130': "V2 API Nonce value must be a positive integer",
    '131': "V2 API Nonce is must be bigger then last nonce",
    '132': "V2 API body is corrupted",
    '150': "It's V1 API. V2 Access token is not acceptable",
    '151': "It's V2 API. V1 Access token is not acceptable",
    '200': "Wallet Error",
    '202': "Limitation error",
    '210': "Limitation error",
    '220': "Limitation error",
    '221': "Limitation error",
    '310': "Mobile auth error",
    '311': "Need mobile auth",
    '312': "Name is not correct",
    '330': "Phone number error",
    '404': "Page not found error",
    '405': "Server error",
    '444': "Locking error",
    '500': "Email error",
    '501': "Email error",
    '777': "Mobile auth error",
    '778': "Phone number error",
    '1202': "App not found",
    '1203': "Already registered",
    '1204': "Invalid access",
    '1205': "API Key error",
    '1206': "User not found",
    '1207': "User not found",
    '1208': "User not found",
    '1209': "User not found"
}

# log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# logging.basicConfig(format=log_format, level=logging.DEBUG)
# logger = logging.getLogger(__name__)


class Coinone(object):
    def __init__(self, key, secret):
        self.exid = "coinone"
        self.key = key
        self.secret = secret
        # self.default_payload = {"access_token": self.key}
        self.targetBalance = 0
        self.baseBalance   = 0
        self.askprice      = 0
        self.bidprice      = 0
        self.askqty        = 0
        self.bidqty        = 0
        self.taker_fee     = 0.0010
        self.maker_fee     = 0.0010
        self.BCH           = 0.01  # min tradable volume
        self.BTC           = 0.0001
        self.ETH           = 0.01
        self.ETC           = 0.1  # confirm
        self.QTUM          = 0.01
        self.XRP           = 1
        self.LTC           = 0.01
        self.timeout       = 4

    def info(self):
        return self._post('v2/account/user_info')

    def balance(self):
        return self._post('v2/account/balance')

    def daily_balance(self):
        return self._post('v2/account/daily_balance')

    def deposit_address(self):
        return self._post('v2/account/deposit_address')

    def virtual_account(self):
        return self._post('v2/account/virtual_account')

    def orderbook(self, currency='btc'):
        payload = {'currency': currency}
        return self.public_query('orderbook', payload)

    def orders(self, currency='btc'):
        payload = {'access_token' : self.key, 'currency': currency}
        return self._post('v2/order/limit_orders', payload)['limitOrders']

    def complete_orders(self, currency='btc'):
        payload = {'access_token' : self.key, 'currency': currency}
        return self._post('v2/order/complete_orders', payload)['completeOrders']

    def order_info(self, currency='btc', order_id=None):
        payload = {'access_token' : self.key, 'currency': currency, 'order_id': order_id}
        return self._post('v2/order/query_order', payload)

    def cancel(self, currency='btc', order_id=None, price=None, qty=None, is_ask=None):
        """
        cancel an order.
        If all params are empty, it will cancel all orders.
        """
        payload = {'access_token' : self.key,
                   'qty': qty,
                   'order_id': order_id,
                   'currency': currency}
        url = 'v2/order/cancel'
        return self._post(url, payload)

    def buy(self, currency, qty=None, price=None):
        """
        make a buy order.
        if quantity is not given, it will make a market price order.
        """
        payload = {'access_token' : self.key,
                   'price': price,
                   'qty': qty,
                   'currency': currency.lower()}
        url = 'v2/order/limit_buy'
        response = self._post(url, payload)
        status = "OK" if response["result"] == "success" else "ERROR"
        orderNumber = response.get("orderId", 0)
        return status, orderNumber, response

    def sell(self, currency, qty=None, price=None):
        """
        make a sell order.
        if price is not given, it will make a market price order.
        """
        payload = {'access_token' : self.key,
                   'price': price,
                   'qty': qty,
                   'currency': currency.lower()}
        url = 'v2/order/limit_sell'
        # logger.debug('Sell: %s' % payload)
        response = self._post(url, payload)
        status = "OK" if response["result"] == "success" else "ERROR"
        orderNumber = response.get("orderId", 0)
        return status, orderNumber, response

    """
    URL = 'https://api.coinone.co.kr/v2/transaction/coin/'
        PAYLOAD = {
        "access_token": ACCESS_TOKEN,
        "address": "receiver address",
        "auth_number": 123456,
        "qty": 0.1,
        "currency": "btc",
        }
    """

    def auth_number(self, currency):
        payload = {'access_token' : self.key,
                   "type": currency,
                   }
        url = 'v2/transaction/auth_number/'
        response = self._post(url, payload)
        status = "OK" if response["result"] == "success" else "ERROR"
        return status, response

    #i have to wait to be opened 2017.09.04
    def send_coin(self, currency, dest_address, units):
        payload = {'access_token' : self.key,
                   "address"    : dest_address,
                   "qty"        : units,   #float
                   "currency"   : currency,
                   "auth_number": '543256'
                   }
        url = 'v2/transaction/coin'
        response = self._post(url, payload)
        status = "OK" if response["result"] == "success" else "ERROR"
        return status, response

    def send_btc(self, currency, dest_address, from_address, units):
        payload = {'access_token' : self.key,
                   "address"    : dest_address,
                   "qty"        : units,   #float
                   "type"       : 'trade',
                   "currency"   : currency,
                   "auth_number": 543256,
                   "from_address" : from_address,
                   }
        url = 'v2/transaction/btc'
        response = self._post(url, payload)
        status = "OK" if response["result"] == "success" else "ERROR"
        return status, response

    def public_query(self, endpoint, params={}):
        url = base_url + endpoint
        response = None
        try:
            # ret = urllib.request.urlopen(urllib.request.Request(url), timeout=self.timeout)
            response = requests.get(url, params=params, timeout=self.timeout)
            if response.status_code == 200:
                response = response.json()
                return response
            # return json.loads(ret.read())
        except Exception as ex:
            print(f"public query failed_{ex}_{response}")
        return False

    def encode_payload(self, payload):
        payload[u'nonce'] = int(time.time()*1000)
        ret = json.dumps(payload).encode()
        return base64.b64encode(ret)

    def get_signature(self, encoded_payload, secret_key):
        signature = hmac.new(secret_key.upper().encode(), encoded_payload, hashlib.sha512)
        return signature.hexdigest()

    def get_response(self, url, payload, key):
        encoded_payload = self.encode_payload(payload)
        headers = {
            'Content-type': 'application/json',
            'X-COINONE-PAYLOAD': encoded_payload,
            'X-COINONE-SIGNATURE': self.get_signature(encoded_payload, key)
        }
        response = None
        try:
            response = requests.post(url, data=encoded_payload, headers=headers, timeout=self.timeout)
            if response.status_code == 200:
                response = response.json()
                return response
        except Exception as ex:
            print(f'request post_{ex}_{response}')
        return response

    def _post(self, url, payload=None):

        if payload is None:
            payload = {'access_token': self.key}
        res = ""
        try:
            res = self.get_response(base_url+url, payload, self.secret)
            # res = json.loads(res)
            if res['result'] == 'error':
                err = res['errorCode']
                # raise Exception(int(err), error_code[err])
                print("error raised - {%d}-{%d}" % (int(err), error_code[err]))
        except Exception as ex:
            print(f"coinone get response error_{ex}")
        return res

    def get_order_info(self, currency):
        marketinfo = self.orderbook(currency)
        self.askprice = float(marketinfo['ask'][0]['price'])
        self.askqty   = float(marketinfo['ask'][0]['qty'])
        self.bidprice = float(marketinfo['bid'][0]['price'])
        self.bidqty   = float(marketinfo['bid'][0]['qty'])


    def get_balance_info(self, currency):
        try:
            balance = self.balance()
            self.targetBalance = float(balance[currency.lower()]["avail"])
            self.baseBalance   = float(balance['krw'.lower()]["avail"])
            # logging.info("**{} : (tBal: {:.8f}) | (pBal: {:.4f})**"
            #         .format(self.exid, self.targetBalance, self.baseBalance))
        except:
            logging.debug("get_balance_info error occurred")

    def review_cancel_order(self, orderNumber, type, currency, price, qty):
        units_traded = 0
        resp = self.order_info(currency, orderNumber)
        print("co: response %s" % resp)
        if resp["result"] == "success" :
            status = resp['status']
            if  status != 'filled':
                units_traded = qty - float(resp["remainQty"])
                print("units_traded %.4f" % units_traded)
                is_ask = 1 if type == "ask" else 0
                resp = self.cancel(currency, orderNumber, price, qty, is_ask) # type1 is ask, 0 is bid
                print("co: cancel %s" % resp)
                return "NG", (qty - units_traded)
            else: # filled
                return "GO", qty
        print("fail reason %s" % resp)
        return "NG", 0.0

