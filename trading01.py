#!/usr/bin/env python
# 이 프로그램은 빗썸과 코인원간 거래 데모 프로그램이다.

import logging
import logging.handlers
import time

from bithumb import Bithumb
from coinone import Coinone


from configparser import ConfigParser, NoSectionError


class Coin(object):
    def __init__(self):
        self.trade_max_volume = 0
        self.trade_min_thresh = 0
        self.targetSum        = 0
        self.baseSum          = 0
        self.targetCurrency   = 'BTC'
        self.baseCurrency     = 'KRW'
        self.paymentCurrency  = 'KRW'
        self.profit = 0
        self.hit = 0
        self.temp_interval    =  0
        self.update_delay     = 10  # sec
        self.last_update      = 0
        self.bithumb_enabled  = False
        self.traded           = False
        self.dryrun           = 0   # 1: simultation, 0 : real
        self.rate             = 1.001
        self.interval         = 5
        self.max              = 0
        self.thresh           = 0
        self.loop_number      = 0
        self.observer = []


    def cal_profit(self, _from, _to):
        #from: ask market, buy  exchanger
        #to  : bid market, sell exchanger

        #determine tradesize
        TradeSize = min(_from.askqty, _to.bidqty, self.trade_max_volume)

        SellBalance = _to.targetBalance
        BuyBalance  = _from.baseBalance

        if TradeSize > SellBalance :
            TradeSize = SellBalance
        if TradeSize * _from.askprice > BuyBalance :
            TradeSize = BuyBalance / _from.askprice
        TradeSize = int(TradeSize) #truncate under point
        Profit    = TradeSize *(_to.bidprice - _from.askprice) - TradeSize*2*0.001
        return TradeSize, Profit

    def main(self):

        # Create Logger
        logger = logging.getLogger()
        logger.setLevel(logging.NOTSET)
        # Create console handler and set level to debug
        sh = logging.StreamHandler()
        sh.setLevel(logging.DEBUG)
        # Create file handler and set level to debug
        fh = logging.FileHandler('mylog.txt', mode='a')
        fh.setLevel(logging.INFO)

        # Create formatter
        #formatter = logging.Formatter('%(asctime)s %(filename)s %(message)s')
        formatter = logging.Formatter('%(asctime)s %(message)s')
        # Add formatter to handlers
        sh.setFormatter(formatter)
        fh.setFormatter(formatter)

        # Add handlers to logger
        logger.addHandler(sh)
        logger.addHandler(fh)

        # Load Config File
        config = ConfigParser()
        config.read('trading.conf')

        bithumbKey = config.get('ArbBot', 'bithumbKey')
        bithumbSecret = config.get('ArbBot', 'bithumbSecret')
        coinoneKey = config.get('ArbBot', 'coinoneKey')
        coinoneSecret = config.get('ArbBot', 'coinoneSecret')

        chat_id = config.get('ChatBot', 'chatId')
        chat_token = config.get('ChatBot', 'chatToken')

        coin_name = config.get('ArbBot', 'Coin')
        self.trade_max_volume = (float)(config.get(coin_name, 'TRADE_MAX_VOLUME'))
        self.trade_min_thresh = (float)(config.get(coin_name,'TRADE_MIN_THRESH'))

        self.dryrun = (int)(config.get('ArbBot', 'dryrun'))


        # Load Configuration
        self.targetCurrency  = coin_name
        self.baseCurrency    = 'KRW'
        self.paymentCurrency = 'KRW'

        # Create Exchange API Objects
        bithumb = Bithumb(bithumbKey, bithumbSecret)
        coinone = Coinone(coinoneKey, coinoneSecret)

        # Main Loop

        #check balance bithumb and coinone
        print("===check balance")
        response = bithumb.balance(self.targetCurrency)
        status = 'OK' if response['status'] == "0000" else "ERROR"
        print(status)
        bithumb.targetBalance = (float)(response["data"]["available_" + self.targetCurrency.lower()])
        bithumb.baseBalance   = (float)(response["data"]["available_" + self.baseCurrency.lower()])
        logging.info("**{} : (tBal: {:.8f}) | (pBal: {:.4f})**"
              .format("bithumb", bithumb.targetBalance, bithumb.baseBalance))


        #coinone
        response = coinone.balance()
        status = 'OK' if response['errorCode'] == "0" else "ERROR"
        print(status)
        coinone.targetBalance = (float)(response[self.targetCurrency.lower()]["avail"])
        coinone.baseBalance   = (float)(response[self.baseCurrency.lower()]["avail"])
        logging.info("**{} : (tBal: {:.8f}) | (pBal: {:.4f})**"
                     .format("coinone", coinone.targetBalance, coinone.baseBalance))

        if self.dryrun:
            bithumb.targetBalance = 100
            bithumb.baseBalance   = 100000000
            coinone.targetBalance = 100
            coinone.baseBalance   = 100000000

        while True:
            #check price the target
            response = bithumb.orderbook(self.targetCurrency)
            bithumb.askprice = float(response["data"]["asks"][0]["price"])
            bithumb.bidprice = float(response["data"]["bids"][0]["price"])
            bithumb.askqty   = float(response["data"]["asks"][0]["quantity"])
            bithumb.bidqty   = float(response["data"]["bids"][0]["quantity"])
            logging.info("**{} : ask {:.0f} bid {:.0f} askqty {:.4f} bidqty {:.4f}"
                         .format("bithumb", bithumb.askprice,bithumb.bidprice, \
                         bithumb.askqty,bithumb.bidqty ))

            response = coinone.orderbook(self.targetCurrency)
            coinone.askprice = float(response['ask'][0]['price'])
            coinone.askqty   = float(response['ask'][0]['qty'])
            coinone.bidprice = float(response['bid'][0]['price'])
            coinone.bidqty   = float(response['bid'][0]['qty'])
            logging.info("**{} : ask {:.0f} bid {:.0f} askqty {:.4f} bidqty {:.4f}"
                         .format("coinone", coinone.askprice,coinone.bidprice, \
                         coinone.askqty,coinone.bidqty ))

            #test s
            # bithumb.askprice = 950
            # coinone.bidprice = 960
            #test e

            #find the chance
            if bithumb.askprice < coinone.bidprice:
                logging.info("do trading bithumb buy coinone sell !!!")
                TradeSize, Profit = self.cal_profit(bithumb, coinone)
                self.trade_min_thresh = 10
                if TradeSize > self.trade_min_thresh and Profit > 0:
                    print("start trading1 TS[%d] Profit[%d]" % (TradeSize, Profit))
                    if self.dryrun==0:
                        bithumb.buy(self.targetCurrency, TradeSize,bithumb.askprice)
                        coinone.sell(self.targetCurrency, TradeSize, coinone.bidprice)
                else:
                    print("skip trading1 TS[%d] Profit[%d]" %(TradeSize, Profit))
            elif coinone.askprice < bithumb.bidprice:
                logging.info("do trading coinone buy bithumb sell !!!")
                TradeSize, Profit = self.cal_profit(coinone, bithumb)
                self.trade_min_thresh = 10
                if TradeSize > self.trade_min_thresh and Profit > 10:
                    print("start trading2 TS[%d] Profit[%d]" % (TradeSize, Profit))
                    if self.dryrun==0:
                        coinone.buy(self.targetCurrency, TradeSize, coinone.askprice)
                        bithumb.sell(self.targetCurrency, TradeSize, bithumb.bidprice)
                else:
                    print("skip trading2 TS[%d] Profit[%d]" % (TradeSize, Profit))
            else:
                logging.info("..")

            time.sleep(5)

if __name__ == "__main__":
    print("Arbitrage start")
    coin = Coin()
    coin.main()